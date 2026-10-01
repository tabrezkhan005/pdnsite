import logging
from datetime import timedelta

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from .models import FeePlan, Invoice, StudentFeeAssignment
from .services import apply_late_fees, generate_invoices_for_period

logger = logging.getLogger(__name__)

@shared_task
def generate_recurring_invoices(days_ahead=7):
    """
    Generates invoices for active assignments 'days_ahead' before the period starts.
    Safe to run twice (idempotent).
    """
    today = timezone.now().date()
    target_date = today + timedelta(days=days_ahead)

    assignments = StudentFeeAssignment.objects.filter(
        status=StudentFeeAssignment.Status.ACTIVE,
        start_date__lte=target_date
    ).exclude(
        end_date__lt=target_date
    ).select_related('fee_plan', 'student', 'student__guardian')

    for assignment in assignments:
        plan = assignment.fee_plan

        # Calculate period_start and period_end based on target_date and plan frequency
        # For simplicity, assuming monthly plans start on the 1st
        # In a real app, you'd align this with assignment.start_date
        period_start = target_date.replace(day=1)

        if plan.frequency == FeePlan.Frequency.MONTHLY:
            period_end = period_start + relativedelta(months=1, days=-1)
        elif plan.frequency == FeePlan.Frequency.QUARTERLY:
            period_end = period_start + relativedelta(months=3, days=-1)
        elif plan.frequency == FeePlan.Frequency.ANNUAL:
            period_end = period_start + relativedelta(years=1, days=-1)
        else:
            continue # ONE_TIME are generated manually or via specific trigger

        # Due date based on plan
        due_date = period_start.replace(day=min(plan.due_day_of_period, 28))

        try:
            generate_invoices_for_period(
                assignment=assignment,
                period_start=period_start,
                period_end=period_end,
                issue_date=today,
                due_date=due_date
            )
        except Exception as e:
            logger.exception(f"Failed to generate invoice for assignment {assignment.id}: {e}")

@shared_task
def apply_late_fees_task():
    """
    Marks overdue invoices and applies late fees if grace period has passed.
    """
    today = timezone.now().date()

    invoices = Invoice.objects.filter(
        status__in=[Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID],
        due_date__lt=today
    ).select_related('fee_plan')

    for invoice in invoices:
        try:
            apply_late_fees(invoice)
        except Exception as e:
            logger.exception(f"Failed to apply late fee to invoice {invoice.id}: {e}")
