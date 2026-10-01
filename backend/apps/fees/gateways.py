import hashlib
import hmac

import razorpay
from django.conf import settings


class PaymentGateway:
    def create_order(self, amount_paise, receipt_ref, notes=None):
        raise NotImplementedError

    def verify_webhook_signature(self, body_bytes, signature):
        raise NotImplementedError

    def verify_checkout_signature(self, order_id, payment_id, signature):
        raise NotImplementedError

    def fetch_payment(self, payment_id):
        raise NotImplementedError

    def refund_payment(self, payment_id, amount_paise=None):
        raise NotImplementedError

class RazorpayGateway(PaymentGateway):
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    def create_order(self, amount_paise, receipt_ref, notes=None):
        data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt_ref,
            "notes": notes or {}
        }
        order = self.client.order.create(data=data)
        return order['id']

    def verify_webhook_signature(self, body_bytes, signature):
        expected_sig = hmac.new(
            self.webhook_secret.encode('utf-8'),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def verify_checkout_signature(self, order_id, payment_id, signature):
        msg = f"{order_id}|{payment_id}"
        expected_sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def fetch_payment(self, payment_id):
        return self.client.payment.fetch(payment_id)

    def refund_payment(self, payment_id, amount_paise=None):
        data = {}
        if amount_paise:
            data['amount'] = amount_paise
        return self.client.payment.refund(payment_id, data)

class FakeGateway(PaymentGateway):
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def create_order(self, amount_paise, receipt_ref, notes=None):
        order_id = f"order_fake_{len(self.orders)+1}"
        self.orders[order_id] = {
            "amount": amount_paise,
            "receipt": receipt_ref
        }
        return order_id

    def verify_webhook_signature(self, body_bytes, signature):
        return signature == "fake_valid_signature"

    def verify_checkout_signature(self, order_id, payment_id, signature):
        return signature == "fake_valid_signature"

    def fetch_payment(self, payment_id):
        return self.payments.get(payment_id, {"status": "captured"})

    def refund_payment(self, payment_id, amount_paise=None):
        return {"id": f"rfnd_{payment_id}", "status": "processed"}

def get_gateway():
    if getattr(settings, 'USE_FAKE_PAYMENT_GATEWAY', False):
        return FakeGateway()
    return RazorpayGateway()
