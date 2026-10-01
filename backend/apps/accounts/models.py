import uuid
from datetime import date

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from apps.academics.models import Branch
from common.models import SoftDeleteModel, TimeStampedModel


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        STUDENT = "STUDENT", "Student"
        GUARDIAN = "GUARDIAN", "Guardian"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="Phone number with country code, e.g. +919876543210",
    )

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class GuardianProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardian_profile")
    relationship_note = models.CharField(max_length=255, blank=True, help_text="e.g. Mother, Father, Uncle")
    address = models.TextField(blank=True)
    whatsapp_opt_in = models.BooleanField(default=False)
    email_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"Guardian: {self.user.get_full_name()}"


class StudentProfile(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_BREAK = "ON_BREAK", "On Break"
        ALUMNI = "ALUMNI", "Alumni"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="student_profile")
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    guardian = models.ForeignKey(GuardianProfile, on_delete=models.CASCADE, related_name="students")
    secondary_guardian = models.ForeignKey(GuardianProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="secondary_students")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="students")

    student_id = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    joined_on = models.DateField(default=date.today)

    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)

    medical_notes = models.TextField(blank=True, help_text="Staff-visible only.")
    photo_consent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff")
    bio = models.TextField(blank=True)
    is_teacher = models.BooleanField(default=False)
    can_record_payments = models.BooleanField(default=False, help_text="Can record offline payments and access financial data.")

    def __str__(self):
        return f"Staff: {self.user.get_full_name()}"


class StudentIDCounter(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    year = models.IntegerField()
    last_value = models.IntegerField(default=0)

    class Meta:
        unique_together = ("branch", "year")

    def __str__(self):
        return f"{self.branch.code} - {self.year}: {self.last_value}"

    @classmethod
    def generate_id(cls, branch):
        current_year = date.today().year % 100
        branch_code = branch.code or "XXX"

        with transaction.atomic():
            counter, _ = cls.objects.select_for_update().get_or_create(
                branch=branch,
                year=current_year
            )
            counter.last_value += 1
            counter.save()
            seq = counter.last_value

        return f"PDN-{branch_code}-{current_year:02d}-{seq:04d}"


class ConsentRecord(TimeStampedModel):
    class Type(models.TextChoices):
        PHOTO = "PHOTO", "Photo"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        DATA_PROCESSING = "DATA_PROCESSING", "Data Processing"

    guardian = models.ForeignKey(GuardianProfile, on_delete=models.CASCADE, related_name="consents")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="consents", null=True, blank=True)
    consent_type = models.CharField(max_length=50, choices=Type.choices)
    granted = models.BooleanField()
    granted_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=255, help_text="Where was this consent collected?")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-granted_at"]


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)

    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    target_object_id = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    target = GenericForeignKey("target_content_type", "target_object_id")

    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
