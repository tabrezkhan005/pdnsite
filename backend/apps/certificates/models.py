import uuid

from django.db import models

from common.models import TimeStampedModel


class Certificate(TimeStampedModel):
    # A unique code used for public verification, usually shorter than a UUID (e.g., PDN-2023-XXXX)
    # We will just use the uuid string directly for now, or short UUID
    verification_code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    student_name = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255)
    issue_date = models.DateField()
    grade = models.CharField(max_length=50, blank=True)
    pdf_file = models.FileField(upload_to="certificates/", blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Can be used to revoke certificates")

    class Meta(TimeStampedModel.Meta):
        ordering = ["-issue_date", "student_name"]

    def __str__(self):
        return f"Certificate {self.verification_code} - {self.student_name}"
