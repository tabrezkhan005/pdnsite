from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.academics.models import Course, Enrollment, Level
from apps.accounts.models import StudentProfile
from common.models import SoftDeleteModel, TimeStampedModel


class FeePlan(TimeStampedModel, SoftDeleteModel):
    class Frequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        ANNUAL = "ANNUAL", "Annual"
        ONE_TIME = "ONE_TIME", "One Time"

    class LateFeeType(models.TextChoices):
        NONE = "NONE", "None"
        FLAT = "FLAT", "Flat Amount"
        PERCENT = "PERCENT", "Percentage"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="fee_plans")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True, blank=True, related_name="fee_plans")
    name = models.CharField(max_length=255)

    amount_paise = models.PositiveIntegerField(help_text="Amount in paise")
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)

    due_day_of_period = models.PositiveIntegerField(default=1, help_text="Day of the month (e.g. 1st)")
    grace_days = models.PositiveIntegerField(default=5)

    late_fee_type = models.CharField(max_length=20, choices=LateFeeType.choices, default=LateFeeType.NONE)
    late_fee_value = models.PositiveIntegerField(default=0, help_text="Paise for FLAT, basis points (100 = 1%) for PERCENT")

    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    def clean(self):
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValidationError("effective_to cannot be earlier than effective_from")

    def __str__(self):
        return f"{self.name} - {self.course.title} ({self.frequency})"

class FeeItem(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    amount_paise = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Concession(TimeStampedModel, SoftDeleteModel):
    class Type(models.TextChoices):
        SIBLING = "SIBLING", "Sibling"
        SCHOLARSHIP = "SCHOLARSHIP", "Scholarship"
        MANUAL = "MANUAL", "Manual"

    class ValueType(models.TextChoices):
        FLAT = "FLAT", "Flat Amount"
        PERCENT = "PERCENT", "Percentage"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="concessions")
    type = models.CharField(max_length=20, choices=Type.choices)
    value_type = models.CharField(max_length=20, choices=ValueType.choices)
    value = models.PositiveIntegerField(help_text="Paise for FLAT, basis points (100 = 1%) for PERCENT")

    applies_to_plan = models.ForeignKey(FeePlan, on_delete=models.CASCADE, null=True, blank=True, help_text="If null, applies to all plans")

    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    reason = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="approved_concessions")

    def __str__(self):
        return f"{self.type} for {self.student}"

class TaxConfig(TimeStampedModel):
    name = models.CharField(max_length=255, default="GST")
    rate_basis_points = models.PositiveIntegerField(help_text="e.g. 1800 for 18%")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate_basis_points / 100}%)"

class StudentFeeAssignment(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        CANCELLED = "CANCELLED", "Cancelled"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="fee_assignments")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="fee_assignments", null=True, blank=True)
    fee_plan = models.ForeignKey(FeePlan, on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f"{self.fee_plan.name} -> {self.student.full_name}"
