from django.db import models
from django.db.models import Q
from common.models import SoftDeleteModel, TimeStampedModel
from django.core.exceptions import ValidationError

class Branch(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Short code for Student ID (e.g. GNT)", null=True)
    address = models.TextField()
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    map_url = models.URLField(blank=True, help_text="Google Maps embed URL or link")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Branches"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Course(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    duration = models.CharField(max_length=100, help_text="e.g., '6 months', '1 year'")
    # Monthly fee in paise (e.g. 150000 = ₹1500)
    monthly_fee = models.PositiveIntegerField(help_text="Fee in paise (e.g. 150000 = ₹1500)", null=True, blank=True)
    image = models.ImageField(upload_to="courses/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = ["display_order", "title"]

    def __str__(self):
        return self.title


class Faculty(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, help_text="e.g. 'Senior Instructor', 'Director'")
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to="faculty/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Faculty"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Level(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["course", "order"]
        unique_together = ("course", "name")

    def __str__(self):
        return f"{self.course.title} - {self.name}"


class Batch(TimeStampedModel, SoftDeleteModel):
    class Mode(models.TextChoices):
        OFFLINE = "OFFLINE", "Offline"
        ONLINE = "ONLINE", "Online"
        HYBRID = "HYBRID", "Hybrid"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="batches")
    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name="batches")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="batches")
    teacher = models.ForeignKey("accounts.StaffProfile", on_delete=models.PROTECT, related_name="batches")
    
    name = models.CharField(max_length=255)
    # days_of_week stores a list of integers 0-6 where 0=Monday, 6=Sunday
    days_of_week = models.JSONField(help_text="List of integers (0=Mon, 6=Sun)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    capacity = models.PositiveIntegerField()
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.OFFLINE)
    default_meeting_url = models.URLField(blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Batches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.branch.code})"


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        ENDED = "ENDED", "Ended"

    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="enrollments")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_on = models.DateField(auto_now_add=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        # Enforce one ACTIVE enrollment per student per batch
        constraints = [
            models.UniqueConstraint(
                fields=["student", "batch"],
                condition=Q(status="ACTIVE"),
                name="unique_active_enrollment_per_student_batch"
            )
        ]
        ordering = ["-enrolled_on"]

    def __str__(self):
        return f"{self.student} in {self.batch} ({self.status})"


class Holiday(TimeStampedModel):
    date = models.DateField(db_index=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name="holidays", help_text="Null means all branches")
    reason = models.CharField(max_length=255)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - {self.reason}"


class ClassSession(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"
        
    class Mode(models.TextChoices):
        OFFLINE = "OFFLINE", "Offline"
        ONLINE = "ONLINE", "Online"
        HYBRID = "HYBRID", "Hybrid"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="sessions")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    mode = models.CharField(max_length=20, choices=Mode.choices)
    meeting_url = models.URLField(blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    is_makeup = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "starts_at"],
                name="unique_batch_session_start"
            )
        ]

    def __str__(self):
        return f"{self.batch.name} on {self.starts_at.date()}"
