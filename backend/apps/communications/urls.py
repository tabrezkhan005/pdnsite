from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdmissionEnquiryViewSet, ContactMessageViewSet

router = DefaultRouter()
router.register(r'enquiries', AdmissionEnquiryViewSet, basename="enquiry")
router.register(r'contact', ContactMessageViewSet, basename="contact")

urlpatterns = [
    path('', include(router.urls)),
]
