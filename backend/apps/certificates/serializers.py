from rest_framework import serializers

from .models import Certificate


class CertificateVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ["verification_code", "student_name", "course_name", "issue_date", "grade", "pdf_file"]
