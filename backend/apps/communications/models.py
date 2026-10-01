from django.db import models

from common.models import TimeStampedModel


class AdmissionEnquiry(TimeStampedModel):
    STATUS_CHOICES = (
        ("NEW", "New"),
        ("CONTACTED", "Contacted"),
        ("ENROLLED", "Enrolled"),
        ("CLOSED", "Closed"),
    )

    student_name = models.CharField(max_length=255)
    parent_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50)
    course_interest = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    internal_notes = models.TextField(blank=True)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Admission Enquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Enquiry: {self.student_name} ({self.status})"


class ContactMessage(TimeStampedModel):
    STATUS_CHOICES = (
        ("NEW", "New"),
        ("READ", "Read"),
        ("REPLIED", "Replied"),
    )

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")

    class Meta(TimeStampedModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
