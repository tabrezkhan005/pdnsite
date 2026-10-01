import json

from django.db import transaction
from django.utils import timezone

from apps.accounts.services import log_audit_event

from .gateways import get_gateway
from .models import Allocation, Invoice, Payment, PaymentEvent


def create_payment_order(student, amount_paise, invoice_ids=None):
    """
    Creates a Payment record and corresponding Razorpay Order.
    """
    if invoice_ids:
        invoices = Invoice.objects.filter(id__in=invoice_ids, student=student)
        total_balance = sum(inv.balance_paise for inv in invoices)
        if amount_paise > total_balance:
            raise ValueError("Payment amount cannot exceed total invoice balance.")

    with transaction.atomic():
        payment = Payment.objects.create(
            student=student,
            amount_paise=amount_paise,
            method=Payment.Method.ONLINE,
            status=Payment.Status.CREATED
        )

        gateway = get_gateway()
        # Create RZP Order
        receipt_ref = f"PDN_PAY_{payment.id}"
        order_id = gateway.create_order(
            amount_paise=amount_paise,
            receipt_ref=receipt_ref,
            notes={"payment_id": str(payment.id)}
        )

        payment.razorpay_order_id = order_id
        payment.save(update_fields=['razorpay_order_id'])

    return payment

def handle_payment_webhook(raw_payload_bytes, signature_header):
    """
    Idempotent webhook handler. 
    """
    gateway = get_gateway()
    if not gateway.verify_webhook_signature(raw_payload_bytes, signature_header):
        raise ValueError("Invalid signature")

    payload = json.loads(raw_payload_bytes)
    event_id = payload.get("id")
    event_type = payload.get("event")

    # Check idempotency
    if PaymentEvent.objects.filter(event_id=event_id).exists():
        return # Already processed

    payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_data.get("order_id")
    amount = payment_data.get("amount")

    if not order_id:
        # We only care about orders we generated
        return

    with transaction.atomic():
        # Lock payment
        payment = Payment.objects.select_for_update().filter(razorpay_order_id=order_id).first()
        if not payment:
            return

        event = PaymentEvent.objects.create(
            payment=payment,
            source=PaymentEvent.Source.WEBHOOK,
            event_id=event_id,
            event_type=event_type,
            raw_payload=payload
        )

        try:
            if event_type == "payment.captured" or event_type == "order.paid":
                _process_successful_payment(payment, payment_data)
            elif event_type == "payment.failed":
                payment.status = Payment.Status.FAILED
                payment.failure_reason = payment_data.get("error_description", "Unknown error")
                payment.save(update_fields=['status', 'failure_reason'])

            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])

        except Exception as e:
            event.processing_error = str(e)
            event.save(update_fields=['processing_error'])
            raise

def _process_successful_payment(payment, rzp_payment_entity):
    if payment.status == Payment.Status.CAPTURED:
        return

    payment.razorpay_payment_id = rzp_payment_entity.get("id")
    payment.razorpay_method_detail = rzp_payment_entity.get("method")
    payment.captured_at = timezone.now()

    amount_paid = rzp_payment_entity.get("amount")

    if amount_paid != payment.amount_paise:
        payment.is_amount_mismatch = True
        payment.status = Payment.Status.CAPTURED
        payment.save()
        # Do not auto-allocate on mismatch
        return

    payment.status = Payment.Status.CAPTURED
    payment.save()

    # Auto-allocate to oldest unpaid invoices for student
    _auto_allocate_payment(payment)

def _auto_allocate_payment(payment):
    remaining = payment.amount_paise

    invoices = Invoice.objects.filter(
        student=payment.student,
        status__in=[Invoice.Status.ISSUED, Invoice.Status.OVERDUE, Invoice.Status.PARTIALLY_PAID]
    ).order_by('issue_date')

    for inv in invoices:
        if remaining <= 0:
            break

        alloc_amount = min(remaining, inv.balance_paise)
        if alloc_amount > 0:
            Allocation.objects.create(
                payment=payment,
                invoice=inv,
                amount_paise=alloc_amount
            )
            inv.paid_paise += alloc_amount
            inv.balance_paise -= alloc_amount
            if inv.balance_paise == 0:
                inv.status = Invoice.Status.PAID
            else:
                inv.status = Invoice.Status.PARTIALLY_PAID
            inv.save(update_fields=['paid_paise', 'balance_paise', 'status'])

            remaining -= alloc_amount

def record_offline_payment(student, amount_paise, method, user, reference_note=None):
    with transaction.atomic():
        payment = Payment.objects.create(
            student=student,
            amount_paise=amount_paise,
            method=method,
            status=Payment.Status.CAPTURED,
            captured_at=timezone.now(),
            recorded_by=user,
            reference_note=reference_note
        )

        PaymentEvent.objects.create(
            payment=payment,
            source=PaymentEvent.Source.ADMIN,
            event_type="offline_payment",
            raw_payload={"amount": amount_paise, "method": method, "recorded_by": str(user.id)},
            processed_at=timezone.now()
        )

        _auto_allocate_payment(payment)

        log_audit_event(
            actor=user,
            action="RECORDED_OFFLINE_PAYMENT",
            target=payment,
            after_state={"amount": amount_paise, "method": method}
        )
        return payment
