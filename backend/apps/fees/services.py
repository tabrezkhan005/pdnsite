from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.services import log_audit_event

from .models import Adjustment, Concession, FeePlan, Invoice, InvoiceLine, TaxConfig


def create_fee_plan_version(old_plan, new_amount_paise, effective_from):
    """
    Creates a new version of a FeePlan by ending the old one and starting a new one.
    """
    with transaction.atomic():
        old_plan.effective_to = effective_from
        old_plan.save()

        new_plan = FeePlan.objects.create(
            course=old_plan.course,
            level=old_plan.level,
            name=old_plan.name,
            amount_paise=new_amount_paise,
            frequency=old_plan.frequency,
            due_day_of_period=old_plan.due_day_of_period,
            grace_days=old_plan.grace_days,
            late_fee_type=old_plan.late_fee_type,
            late_fee_value=old_plan.late_fee_value,
            effective_from=effective_from,
            is_active=True
        )
        return new_plan

def calculate_percentage_amount(base_amount_paise, basis_points):
    """
    SINGLE SOURCE OF TRUTH FOR PERCENTAGE ROUNDING.
    Calculates the percentage of an amount in paise.
    Rounding uses ROUND_HALF_UP to the nearest integer paisa.
    Formula: amount * (basis_points / 10000)
    """
    amount = Decimal(base_amount_paise) * Decimal(basis_points) / Decimal(10000)
    return int(amount.quantize(Decimal('1.'), rounding=ROUND_HALF_UP))

def calculate_concession(concession, amount_paise):
    """
    Calculates the discount amount in paise for a given concession against a base amount.
    """
    if concession.value_type == Concession.ValueType.FLAT:
        return min(concession.value, amount_paise)

    # PERCENT: value is in basis points (100 = 1%)
    return min(calculate_percentage_amount(amount_paise, concession.value), amount_paise)

def apply_concessions(student, fee_plan, amount_paise, target_date):
    """
    Finds applicable concessions for a student on a specific date and fee plan.
    Returns the total discount in paise.
    """
    # Active concessions on target_date
    concessions = Concession.objects.filter(
        student=student,
        valid_from__lte=target_date
    )

    applicable = []
    for c in concessions:
        if c.valid_to and c.valid_to < target_date:
            continue
        if c.applies_to_plan and c.applies_to_plan != fee_plan:
            continue
        applicable.append(c)

    total_discount = 0
    # Apply concessions cumulatively? Standard is to apply sequentially or on base.
    # Usually applied to base.
    for c in applicable:
        total_discount += calculate_concession(c, amount_paise)

    return min(total_discount, amount_paise)
def recalculate_invoice_totals(invoice):
    """
    Recalculates the invoice total based on its lines, discounts, tax, and late fees.
    """
    subtotal = sum(line.line_total_paise for line in invoice.lines.all())
    tax = sum(calculate_percentage_amount(line.line_total_paise, line.tax_rate_bp) for line in invoice.lines.all())

    invoice.subtotal_paise = subtotal
    invoice.tax_paise = tax
    invoice.total_paise = subtotal - invoice.discount_paise + tax + invoice.late_fee_paise
    invoice.balance_paise = invoice.total_paise - invoice.paid_paise
    invoice.save(update_fields=['subtotal_paise', 'tax_paise', 'total_paise', 'balance_paise'])

def generate_invoices_for_period(assignment, period_start, period_end, issue_date, due_date):
    """
    Idempotent function to generate an invoice for a specific StudentFeeAssignment for a given period.
    """
    student = assignment.student
    fee_plan = assignment.fee_plan
    guardian = student.guardian

    with transaction.atomic():
        invoice, created = Invoice.objects.get_or_create(
            student=student,
            fee_plan=fee_plan,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'guardian': guardian,
                'issue_date': issue_date,
                'due_date': due_date,
                'status': Invoice.Status.DRAFT,
            }
        )

        if not created and invoice.status != Invoice.Status.DRAFT:
            # Invoice already exists and is not draft. Do not modify.
            return invoice

        # Calculate base fee
        amount_paise = fee_plan.amount_paise

        # Calculate discount
        discount_paise = apply_concessions(student, fee_plan, amount_paise, issue_date)

        invoice.discount_paise = discount_paise
        invoice.save(update_fields=['discount_paise'])

        # Get tax config
        tax_config = TaxConfig.objects.filter(is_active=True).first()
        tax_rate = tax_config.rate_basis_points if tax_config else 0

        # Create line
        InvoiceLine.objects.update_or_create(
            invoice=invoice,
            source_type=InvoiceLine.SourceType.PLAN,
            source_id=str(fee_plan.id),
            defaults={
                'description': f"{fee_plan.name} for {period_start} to {period_end}",
                'quantity': 1,
                'unit_amount_paise': amount_paise,
                'line_total_paise': amount_paise,
                'tax_rate_bp': tax_rate
            }
        )

        recalculate_invoice_totals(invoice)

        # Issue the invoice
        invoice.status = Invoice.Status.ISSUED
        invoice.save(update_fields=['status', 'invoice_number'])

        log_audit_event(
            actor=None, # System task
            action="INVOICE_ISSUED",
            target=invoice,
            after_state={"amount": invoice.total_paise}
        )

    return invoice

def apply_late_fees(invoice):
    """
    Idempotent function to apply a late fee to an overdue invoice.
    """
    if invoice.status not in (Invoice.Status.OVERDUE, Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID):
        return

    plan = invoice.fee_plan
    if not plan or plan.late_fee_type == FeePlan.LateFeeType.NONE:
        return

    today = timezone.now().date()
    grace_date = invoice.due_date
    from datetime import timedelta
    if grace_date:
        grace_date += timedelta(days=plan.grace_days)

    if grace_date and today > grace_date:
        if invoice.late_fee_paise > 0:
            return # Already applied

        with transaction.atomic():
            late_fee = 0
            if plan.late_fee_type == FeePlan.LateFeeType.FLAT:
                late_fee = plan.late_fee_value
            elif plan.late_fee_type == FeePlan.LateFeeType.PERCENT:
                # Late fee on the remaining balance? Or on the base amount?
                # "late fees apply strictly after the fact to the outstanding balance and do not receive concessions" (PAYMENTS.md)
                late_fee = calculate_percentage_amount(invoice.balance_paise, plan.late_fee_value)

            invoice.late_fee_paise = late_fee
            invoice.status = Invoice.Status.OVERDUE
            invoice.save(update_fields=['late_fee_paise', 'status'])
            recalculate_invoice_totals(invoice)

            log_audit_event(
                actor=None, # System task
                action="INVOICE_LATE_FEE_APPLIED",
                target=invoice,
                after_state={"late_fee": late_fee, "total": invoice.total_paise}
            )

def cancel_invoice(invoice):
    """
    Cancels an invoice only if there are no payments.
    """
    if invoice.paid_paise > 0:
        raise ValueError("Cannot cancel an invoice with payments. Use void_invoice instead.")

    invoice.status = Invoice.Status.CANCELLED
    invoice.save(update_fields=['status'])

    # Ideally should pass user, but this is a simple cancel
    log_audit_event(
        actor=None,
        action="INVOICE_CANCELLED",
        target=invoice,
        after_state={"status": Invoice.Status.CANCELLED}
    )

def void_invoice(invoice, reason, user):
    """
    Voids an invoice by creating an adjustment that zeros out the balance.
    """
    if invoice.balance_paise <= 0:
        return

    with transaction.atomic():
        Adjustment.objects.create(
            invoice=invoice,
            type=Adjustment.Type.CREDIT,
            amount_paise=invoice.balance_paise,
            reason=reason,
            approved_by=user
        )
        invoice.paid_paise += invoice.balance_paise
        invoice.balance_paise = 0
        invoice.status = Invoice.Status.VOID
        invoice.save(update_fields=['paid_paise', 'balance_paise', 'status'])

        log_audit_event(
            actor=user,
            action="INVOICE_VOIDED",
            target=invoice,
            after_state={"reason": reason}
        )

def add_one_time_charge(invoice, fee_item):
    """
    Adds a one-time charge as a new line on an existing DRAFT or ISSUED invoice.
    """
    if invoice.status not in (Invoice.Status.DRAFT, Invoice.Status.ISSUED):
        raise ValueError("Cannot add lines to this invoice.")

    with transaction.atomic():
        tax_config = TaxConfig.objects.filter(is_active=True).first()
        tax_rate = tax_config.rate_basis_points if tax_config else 0

        InvoiceLine.objects.create(
            invoice=invoice,
            source_type=InvoiceLine.SourceType.ITEM,
            source_id=str(fee_item.id),
            description=fee_item.name,
            quantity=1,
            unit_amount_paise=fee_item.amount_paise,
            line_total_paise=fee_item.amount_paise,
            tax_rate_bp=tax_rate
        )
        recalculate_invoice_totals(invoice)

        # In a real app we'd pass user here too, assuming actor=None for simplicity
        log_audit_event(
            actor=None,
            action="INVOICE_ONE_TIME_CHARGE_ADDED",
            target=invoice,
            after_state={"charge": fee_item.amount_paise}
        )

