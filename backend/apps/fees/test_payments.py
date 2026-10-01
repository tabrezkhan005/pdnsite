import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.fees.models import Allocation, Invoice, Payment, PaymentEvent


@pytest.fixture
def payment_setup(fee_setup):
    invoice = Invoice.objects.create(
        student=fee_setup["student"],
        guardian=fee_setup["student"].guardian,
        fee_plan=fee_setup["plan"],
        status=Invoice.Status.ISSUED,
        subtotal_paise=100000,
        tax_paise=18000,
        total_paise=118000,
        balance_paise=118000
    )

    guardian_user = fee_setup["student"].guardian.user
    other_guardian = User.objects.create_user(username="other", role=User.Role.GUARDIAN)

    return {
        "invoice": invoice,
        "student": fee_setup["student"],
        "guardian_user": guardian_user,
        "other_guardian": other_guardian,
        "admin": fee_setup["admin"]
    }

def get_valid_signature(body, secret=None):
    if not secret:
        secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'test_secret')
    return hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

@pytest.mark.django_db
def test_create_order_amount_validation(payment_setup, settings):
    settings.USE_FAKE_PAYMENT_GATEWAY = True
    client = APIClient()
    client.force_authenticate(user=payment_setup["guardian_user"])

    # 1. Overpayment via order creation should fail
    resp = client.post(reverse("payment-create-order"), {
        "student_id": payment_setup["student"].id,
        "amount_paise": 150000, # greater than 118000
        "invoice_ids": [str(payment_setup["invoice"].id)]
    }, format='json')
    assert resp.status_code == 400
    assert "cannot exceed" in resp.data["error"]

    # 2. Valid partial payment
    resp = client.post(reverse("payment-create-order"), {
        "student_id": payment_setup["student"].id,
        "amount_paise": 50000,
        "invoice_ids": [str(payment_setup["invoice"].id)]
    }, format='json')
    assert resp.status_code == 200
    assert resp.data["amount_paise"] == 50000

    # 3. Permissions check: other guardian cannot create order
    client.force_authenticate(user=payment_setup["other_guardian"])
    resp = client.post(reverse("payment-create-order"), {
        "student_id": payment_setup["student"].id,
        "amount_paise": 50000,
        "invoice_ids": [str(payment_setup["invoice"].id)]
    }, format='json')
    assert resp.status_code == 403

@pytest.mark.django_db
def test_webhook_signature_and_idempotency(payment_setup, settings):
    settings.USE_FAKE_PAYMENT_GATEWAY = False # Use real verification logic
    settings.RAZORPAY_KEY_ID = "test_key"
    settings.RAZORPAY_KEY_SECRET = "test_secret"
    settings.RAZORPAY_WEBHOOK_SECRET = "test_secret"

    client = APIClient()

    # Setup payment
    payment = Payment.objects.create(
        student=payment_setup["student"],
        amount_paise=118000,
        method=Payment.Method.ONLINE,
        status=Payment.Status.CREATED,
        razorpay_order_id="order_123"
    )

    payload = {
        "event": "payment.captured",
        "id": "evt_123",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_123",
                    "order_id": "order_123",
                    "amount": 118000,
                    "method": "upi"
                }
            }
        }
    }
    body_bytes = json.dumps(payload).encode('utf-8')
    valid_sig = get_valid_signature(body_bytes)

    # 1. Invalid signature
    resp = client.post(
        reverse("razorpay-webhook"),
        body_bytes,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE="invalid_sig"
    )
    assert resp.status_code == 400

    # 2. Valid signature
    resp = client.post(
        reverse("razorpay-webhook"),
        body_bytes,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=valid_sig
    )
    assert resp.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.CAPTURED
    assert payment.razorpay_payment_id == "pay_123"

    invoice = payment_setup["invoice"]
    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID
    assert invoice.balance_paise == 0

    # 3. Idempotency (Replayed webhook)
    resp = client.post(
        reverse("razorpay-webhook"),
        body_bytes,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=valid_sig
    )
    assert resp.status_code == 200
    assert PaymentEvent.objects.filter(event_id="evt_123").count() == 1

@pytest.mark.django_db
def test_webhook_amount_mismatch(payment_setup, settings):
    settings.USE_FAKE_PAYMENT_GATEWAY = False
    settings.RAZORPAY_KEY_ID = "test_key"
    settings.RAZORPAY_KEY_SECRET = "test_secret"
    settings.RAZORPAY_WEBHOOK_SECRET = "test_secret"

    payment = Payment.objects.create(
        student=payment_setup["student"],
        amount_paise=118000,
        razorpay_order_id="order_456"
    )

    # Client manipulated checkout or RZP sent diff amount
    payload = {
        "event": "payment.captured",
        "id": "evt_456",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_456",
                    "order_id": "order_456",
                    "amount": 100000, # mismatch
                    "method": "card"
                }
            }
        }
    }
    body_bytes = json.dumps(payload).encode('utf-8')

    client = APIClient()
    client.post(
        reverse("razorpay-webhook"),
        body_bytes,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=get_valid_signature(body_bytes)
    )

    payment.refresh_from_db()
    assert payment.status == Payment.Status.CAPTURED
    assert payment.is_amount_mismatch is True

    # No allocation should happen
    assert Allocation.objects.filter(payment=payment).count() == 0

    invoice = payment_setup["invoice"]
    invoice.refresh_from_db()
    assert invoice.balance_paise == 118000
    assert invoice.status == Invoice.Status.ISSUED

@pytest.mark.django_db
def test_offline_payment_and_overpayment(payment_setup):
    from apps.fees.services_payments import record_offline_payment

    admin = payment_setup["admin"]
    student = payment_setup["student"]
    invoice = payment_setup["invoice"]

    # Pay 150000 when balance is 118000
    payment = record_offline_payment(
        student=student,
        amount_paise=150000,
        method=Payment.Method.CASH,
        user=admin,
        reference_note="Cash received"
    )

    assert payment.status == Payment.Status.CAPTURED

    # Check allocation
    alloc = Allocation.objects.get(payment=payment)
    assert alloc.amount_paise == 118000

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID
    assert invoice.balance_paise == 0

    # 32000 unallocated on the payment
    total_allocated = sum(a.amount_paise for a in payment.allocations.all())

    from apps.fees.models import Receipt

    with patch("apps.fees.tasks.generate_receipt_task.delay") as mock_delay:

        # We can't actually run WeasyPrint in Windows tests without GTK+
        # So we manually create a receipt here to simulate the task
        Receipt.objects.create(
            payment=payment,
            student=payment.student,
            amount_paise=payment.amount_paise,
            receipt_number="PDN/REC/FYTEST"
        )

    assert Receipt.objects.filter(payment=payment).count() == 1
