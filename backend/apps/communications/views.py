from rest_framework import mixins, permissions, viewsets

from .models import AdmissionEnquiry, ContactMessage
from .serializers import AdmissionEnquirySerializer, ContactMessageSerializer


class AdmissionEnquiryViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Public API to submit admission enquiries.
    """
    queryset = AdmissionEnquiry.objects.all()
    serializer_class = AdmissionEnquirySerializer
    permission_classes = [permissions.AllowAny]
    # Note: Throttle classes should be added here to prevent spam

class ContactMessageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Public API to submit contact messages.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]
    # Note: Throttle classes should be added here to prevent spam
