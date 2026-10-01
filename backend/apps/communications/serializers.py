from rest_framework import serializers

from .models import AdmissionEnquiry, ContactMessage


class AdmissionEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionEnquiry
        fields = ["student_name", "parent_name", "email", "phone", "course_interest", "message"]

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
