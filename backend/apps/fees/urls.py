from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, PaymentViewSet, razorpay_webhook

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('razorpay/webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('', include(router.urls)),
]
