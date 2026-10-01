from rest_framework import generics, permissions, response, status

from .models import Certificate
from .serializers import CertificateVerificationSerializer


class CertificateVerificationView(generics.GenericAPIView):
    """
    Public API to verify a certificate by its code.
    GET /api/certificates/verify/?code=XYZ
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CertificateVerificationSerializer

    def get(self, request, *args, **kwargs):
        code = request.query_params.get("code")
        if not code:
            return response.Response(
                {"detail": "Verification code is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            certificate = Certificate.objects.get(verification_code=code, is_active=True)
            serializer = CertificateVerificationSerializer(certificate)
            return response.Response(serializer.data)
        except Certificate.DoesNotExist:
            return response.Response(
                {"detail": "Invalid or inactive verification code."},
                status=status.HTTP_404_NOT_FOUND
            )
