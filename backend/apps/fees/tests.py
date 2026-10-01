from datetime import date

import pytest

from apps.fees.models import Concession, FeePlan
from apps.fees.services import apply_concessions, calculate_concession, create_fee_plan_version


@pytest.mark.django_db
def test_fee_plan_versioning(setup_data):
    course = setup_data["course"]
    plan1 = FeePlan.objects.create(
        course=course,
        name="Base Plan",
        amount_paise=100000,
        effective_from=date(2026, 1, 1)
    )

    plan2 = create_fee_plan_version(plan1, 150000, date(2026, 6, 1))

    plan1.refresh_from_db()
    assert plan1.effective_to == date(2026, 6, 1)
    assert plan2.effective_from == date(2026, 6, 1)
    assert plan2.amount_paise == 150000
    assert plan2.name == "Base Plan"

@pytest.mark.django_db
def test_calculate_concession():
    flat_concession = Concession(value_type=Concession.ValueType.FLAT, value=50000)
    assert calculate_concession(flat_concession, 200000) == 50000

    # Exceeding amount
    assert calculate_concession(flat_concession, 30000) == 30000

    # Percent concession: 10% (1000 basis points)
    pct_concession = Concession(value_type=Concession.ValueType.PERCENT, value=1000)
    assert calculate_concession(pct_concession, 150000) == 15000

    # 33.33% = 3333 bp
    pct33 = Concession(value_type=Concession.ValueType.PERCENT, value=3333)
    assert calculate_concession(pct33, 100000) == 33330

@pytest.mark.django_db
def test_apply_concessions(setup_data):
    student = setup_data["student"]
    course = setup_data["course"]
    plan = FeePlan.objects.create(course=course, name="Plan", amount_paise=100000, effective_from=date(2026,1,1))

    Concession.objects.create(
        student=student, type=Concession.Type.SIBLING, value_type=Concession.ValueType.PERCENT, value=1000, valid_from=date(2026, 1, 1)
    )
    Concession.objects.create(
        student=student, type=Concession.Type.MANUAL, value_type=Concession.ValueType.FLAT, value=5000, valid_from=date(2026, 6, 1)
    )

    total = apply_concessions(student, plan, 100000, date(2026, 1, 15))
    assert total == 10000

    total2 = apply_concessions(student, plan, 100000, date(2026, 6, 15))
    assert total2 == 15000
