from django.urls import path

from .views import CertificateVerificationView

urlpatterns = [
    path('verify/', CertificateVerificationView.as_view(), name='certificate-verify'),
]
