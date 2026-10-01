from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

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

class InvoiceCounter(models.Model):
    financial_year = models.CharField(max_length=10) # e.g. "FY2026-27"
    last_value = models.IntegerField(default=0)

    class Meta:
        unique_together = ("financial_year",)

    def __str__(self):
        return f"{self.financial_year}: {self.last_value}"

    @classmethod
    def generate_number(cls):
        from datetime import date
        today = date.today()
        # FY starts in April
        if today.month >= 4:
            fy = f"FY{today.year}-{(today.year+1)%100}"
        else:
            fy = f"FY{today.year-1}-{today.year%100}"

        with transaction.atomic():
            counter, _ = cls.objects.select_for_update().get_or_create(financial_year=fy)
            counter.last_value += 1
            counter.save()
            return f"PDN/{fy}/{counter.last_value:05d}"

class Invoice(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        CANCELLED = "CANCELLED", "Cancelled"
        VOID = "VOID", "Void"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="invoices")
    guardian = models.ForeignKey('accounts.GuardianProfile', on_delete=models.CASCADE, related_name="invoices")
    fee_plan = models.ForeignKey(FeePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    subtotal_paise = models.IntegerField(default=0)
    discount_paise = models.IntegerField(default=0)
    tax_paise = models.IntegerField(default=0)
    late_fee_paise = models.IntegerField(default=0)

    total_paise = models.IntegerField(default=0)
    paid_paise = models.IntegerField(default=0)
    balance_paise = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "fee_plan", "period_start", "period_end"],
                name="unique_invoice_per_student_plan_period",
                condition=models.Q(fee_plan__isnull=False, period_start__isnull=False, period_end__isnull=False)
            )
        ]

    def __str__(self):
        return f"{self.invoice_number or 'DRAFT'} - {self.student.full_name}"

    def save(self, *args, **kwargs):
        # Generate invoice number only upon saving as ISSUED (if not already set)
        if self.status != self.Status.DRAFT and self.status != self.Status.CANCELLED and not self.invoice_number:
            self.invoice_number = InvoiceCounter.generate_number()
        super().save(*args, **kwargs)

class InvoiceLine(TimeStampedModel):
    class SourceType(models.TextChoices):
        PLAN = "PLAN", "Fee Plan"
        ITEM = "ITEM", "Fee Item"
        OTHER = "OTHER", "Other"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_amount_paise = models.IntegerField()
    tax_rate_bp = models.PositiveIntegerField(default=0)
    line_total_paise = models.IntegerField()

    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.OTHER)
    source_id = models.CharField(max_length=50, blank=True) # UUID string or similar

    def __str__(self):
        return f"{self.invoice} - {self.description}"

class Adjustment(TimeStampedModel):
    class Type(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="adjustments")
    type = models.CharField(max_length=20, choices=Type.choices)
    amount_paise = models.PositiveIntegerField()
    reason = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.type} of {self.amount_paise} on {self.invoice}"

class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        CASH = "CASH", "Cash"
        CHEQUE = "CHEQUE", "Cheque"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        UPI_MANUAL = "UPI_MANUAL", "UPI Manual"

    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        PENDING = "PENDING", "Pending"
        CAPTURED = "CAPTURED", "Captured"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="payments")
    amount_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    razorpay_method_detail = models.CharField(max_length=255, blank=True)

    failure_reason = models.TextField(blank=True)
    captured_at = models.DateTimeField(blank=True, null=True)

    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="recorded_payments")
    reference_note = models.TextField(blank=True)

    is_amount_mismatch = models.BooleanField(default=False, help_text="True if webhook amount differs from order amount")

    def __str__(self):
        return f"{self.id} - {self.status} - {self.amount_paise}"

class Allocation(TimeStampedModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="allocations")
    amount_paise = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.amount_paise} from {self.payment.id} to {self.invoice.invoice_number}"

class PaymentEvent(models.Model):
    class Source(models.TextChoices):
        WEBHOOK = "WEBHOOK", "Webhook"
        CHECKOUT = "CHECKOUT", "Checkout"
        RECONCILIATION = "RECONCILIATION", "Reconciliation"
        ADMIN = "ADMIN", "Admin"

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    event_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    event_type = models.CharField(max_length=255)
    raw_payload = models.JSONField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.source} - {self.event_type} - {self.event_id}"
