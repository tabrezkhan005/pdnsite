from datetime import UTC, date

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.fees.models import (
    FeeItem,
    FeePlan,
    Invoice,
    StudentFeeAssignment,
    TaxConfig,
)
from apps.fees.services import (
    add_one_time_charge,
    apply_late_fees,
    cancel_invoice,
    generate_invoices_for_period,
    void_invoice,
)


@pytest.fixture
def fee_setup(setup_data):
    course = setup_data["course"]
    student = setup_data["student"]

    plan = FeePlan.objects.create(
        course=course,
        name="Monthly Fee",
        amount_paise=100000,
        frequency=FeePlan.Frequency.MONTHLY,
        grace_days=5,
        late_fee_type=FeePlan.LateFeeType.FLAT,
        late_fee_value=5000, # 50 rupees
        effective_from=date(2026, 1, 1)
    )

    assignment = StudentFeeAssignment.objects.create(
        student=student,
        fee_plan=plan,
        start_date=date(2026, 1, 1)
    )

    # 18% Tax config
    TaxConfig.objects.create(name="GST", rate_basis_points=1800, is_active=True)

    return {
        "student": student,
        "plan": plan,
        "assignment": assignment,
        "admin": User.objects.create_user(username="admin_user", role=User.Role.ADMIN)
    }

@pytest.mark.django_db
def test_invoice_generation_and_totals(fee_setup):
    assignment = fee_setup["assignment"]

    invoice = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )

    assert invoice.status == Invoice.Status.ISSUED
    assert invoice.invoice_number.startswith("PDN/FY")

    # Check totals
    # Subtotal: 100000
    # Tax: 18% of 100000 = 18000
    # Discount: 0
    # Total: 118000
    assert invoice.subtotal_paise == 100000
    assert invoice.tax_paise == 18000
    assert invoice.discount_paise == 0
    assert invoice.total_paise == 118000
    assert invoice.balance_paise == 118000

    # Idempotency
    invoice2 = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )
    assert invoice.id == invoice2.id
    assert Invoice.objects.count() == 1

@pytest.mark.django_db
def test_apply_late_fees(fee_setup):
    from unittest.mock import patch

    assignment = fee_setup["assignment"]
    invoice = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )

    # Grace period is 5 days, so late after April 6
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = timezone.datetime(2026, 4, 7, tzinfo=UTC)

        apply_late_fees(invoice)

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.OVERDUE
    assert invoice.late_fee_paise == 5000
    assert invoice.total_paise == 118000 + 5000 # subtotal + tax + late_fee

    # Idempotent
    apply_late_fees(invoice)
    assert invoice.late_fee_paise == 5000

@pytest.mark.django_db
def test_cancel_invoice(fee_setup):
    assignment = fee_setup["assignment"]
    invoice = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )

    cancel_invoice(invoice)
    assert invoice.status == Invoice.Status.CANCELLED

    invoice.paid_paise = 100
    with pytest.raises(ValueError):
        cancel_invoice(invoice)

@pytest.mark.django_db
def test_void_invoice(fee_setup):
    assignment = fee_setup["assignment"]
    admin = fee_setup["admin"]
    invoice = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )

    void_invoice(invoice, "Mistake", admin)

    assert invoice.status == Invoice.Status.VOID
    assert invoice.balance_paise == 0
    assert invoice.paid_paise == invoice.total_paise

    adj = invoice.adjustments.first()
    assert adj.amount_paise == 118000
    assert adj.type == "CREDIT"

@pytest.mark.django_db
def test_add_one_time_charge(fee_setup):
    assignment = fee_setup["assignment"]
    invoice = generate_invoices_for_period(
        assignment=assignment,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=date(2026, 3, 25),
        due_date=date(2026, 4, 1)
    )

    item = FeeItem.objects.create(name="Costume", amount_paise=200000)

    add_one_time_charge(invoice, item)

    # Total lines = 2
    assert invoice.lines.count() == 2

    # Recalculated
    # Subtotal: 100000 + 200000 = 300000
    # Tax: 18% of 300000 = 54000
    # Total: 354000
    assert invoice.subtotal_paise == 300000
    assert invoice.tax_paise == 54000
    assert invoice.total_paise == 354000
