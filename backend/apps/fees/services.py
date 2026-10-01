from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from .models import Concession, FeePlan


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

def calculate_concession(concession, amount_paise):
    """
    Calculates the discount amount in paise for a given concession against a base amount.
    Rounding uses ROUND_HALF_UP to the nearest integer.
    """
    if concession.value_type == Concession.ValueType.FLAT:
        return min(concession.value, amount_paise)

    # PERCENT: value is in basis points (100 = 1%)
    # formula: amount * (basis_points / 10000)
    discount = Decimal(amount_paise) * Decimal(concession.value) / Decimal(10000)
    return int(discount.quantize(Decimal('1.'), rounding=ROUND_HALF_UP))

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
