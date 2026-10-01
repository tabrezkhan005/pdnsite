from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.models import StudentProfile
from apps.accounts.scopes import scope_students

from .gateways import get_gateway
from .models import Invoice, Payment
from .services_payments import create_payment_order, handle_payment_webhook


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/payments/invoices/
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Invoice.objects.all()

        if user.role == "STAFF":
            if hasattr(user, 'staff_profile') and user.staff_profile.can_record_payments:
                return Invoice.objects.filter(student__branch=user.staff_profile.branch)
            return Invoice.objects.none()

        students = scope_students(StudentProfile.objects.all(), user)
        return Invoice.objects.filter(student__in=students)

class PaymentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Payment.objects.all()

        students = scope_students(StudentProfile.objects.all(), user)
        return Payment.objects.filter(student__in=students)

    @action(detail=False, methods=['post'], url_path='orders')
    def create_order(self, request):
        """
        POST /api/v1/payments/orders/
        """
        amount_paise = request.data.get("amount_paise")
        invoice_ids = request.data.get("invoice_ids", [])
        student_id = request.data.get("student_id")

        if not amount_paise or not student_id:
            return Response({"error": "amount_paise and student_id are required"}, status=400)

        students = scope_students(StudentProfile.objects.all(), request.user)
        student = students.filter(id=student_id).first()
        if not student:
            return Response({"error": "Invalid student"}, status=403)

        try:
            payment = create_payment_order(student, int(amount_paise), invoice_ids)
            return Response({
                "id": payment.id,
                "razorpay_order_id": payment.razorpay_order_id,
                "amount_paise": payment.amount_paise,
                "status": payment.status
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='orders/confirm')
    def confirm_order(self, request):
        """
        POST /api/v1/payments/orders/confirm/
        """
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing signature parameters"}, status=400)

        gateway = get_gateway()
        if gateway.verify_checkout_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return Response({"status": "Signature verified. Waiting for webhook."})
        else:
            return Response({"error": "Invalid signature"}, status=400)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        GET /api/v1/payments/orders/<id>/
        """
        payment = self.get_object()
        return Response({
            "id": payment.id,
            "status": payment.status,
            "is_amount_mismatch": payment.is_amount_mismatch
        })

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def razorpay_webhook(request):
    """
    POST /api/v1/payments/razorpay/webhook/
    """
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        return Response({"error": "Missing signature"}, status=400)

    try:
        handle_payment_webhook(request.body, signature)
        return Response({"status": "ok"})
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Webhook failed")
        return Response({"error": "Internal server error"}, status=500)
