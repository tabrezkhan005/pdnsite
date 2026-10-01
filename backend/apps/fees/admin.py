from django.contrib import admin

from .models import (
    Adjustment,
    Allocation,
    Concession,
    FeeItem,
    FeePlan,
    Invoice,
    InvoiceCounter,
    InvoiceLine,
    Payment,
    PaymentEvent,
    StudentFeeAssignment,
    TaxConfig,
)


@admin.register(FeePlan)
class FeePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "amount_paise", "frequency", "is_active", "effective_from", "effective_to")
    list_filter = ("frequency", "is_active", "course")
    search_fields = ("name", "course__title")

@admin.register(FeeItem)
class FeeItemAdmin(admin.ModelAdmin):
    list_display = ("name", "amount_paise")
    search_fields = ("name",)

@admin.register(Concession)
class ConcessionAdmin(admin.ModelAdmin):
    list_display = ("student", "type", "value_type", "value", "valid_from", "valid_to")
    list_filter = ("type", "value_type")
    search_fields = ("student__full_name",)

@admin.register(TaxConfig)
class TaxConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "rate_basis_points", "is_active")

@admin.register(StudentFeeAssignment)
class StudentFeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("student", "fee_plan", "start_date", "end_date", "status")
    list_filter = ("status", "fee_plan__frequency")
    search_fields = ("student__full_name",)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "student", "status", "issue_date", "due_date", "total_paise", "balance_paise")
    list_filter = ("status", "issue_date")
    search_fields = ("invoice_number", "student__full_name")

@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "line_total_paise")

@admin.register(InvoiceCounter)
class InvoiceCounterAdmin(admin.ModelAdmin):
    list_display = ("financial_year", "last_value")

@admin.register(Adjustment)
class AdjustmentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "type", "amount_paise", "approved_by")
    list_filter = ("type",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "amount_paise", "method", "status", "captured_at")
    list_filter = ("status", "method", "is_amount_mismatch")
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "student__full_name")

@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "source", "event_type", "received_at", "processed_at")
    list_filter = ("source", "event_type")

@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ("payment", "invoice", "amount_paise")
