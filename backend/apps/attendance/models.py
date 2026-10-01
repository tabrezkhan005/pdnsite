from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from apps.academics.models import ClassSession
from apps.accounts.models import StudentProfile


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual (Teacher)"
        ONLINE_JOIN = "ONLINE_JOIN", "Online Join"
        ADMIN_OVERRIDE = "ADMIN_OVERRIDE", "Admin Override"

    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="attendances")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendances")
    
    status = models.CharField(max_length=20, choices=Status.choices)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "student"], name="unique_attendance_per_student_session")
        ]
        ordering = ["-session__starts_at", "student__full_name"]

    def __str__(self):
        return f"{self.student} - {self.session} ({self.status})"


class SessionJoin(TimeStampedModel):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="joins")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="joins")
    
    joined_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.student} joined {self.session}"


class LeaveRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="leave_requests")
    # session can be null if it's a date-range leave rather than a single session
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, null=True, blank=True, related_name="leave_requests")
    
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_requests_made")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_requests_decided")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Leave for {self.student} ({self.from_date} to {self.to_date})"
