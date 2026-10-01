from datetime import date

import pytest

from apps.accounts.models import User
from apps.fees.models import FeePlan, StudentFeeAssignment, TaxConfig


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
        late_fee_value=5000,
        effective_from=date(2026, 1, 1)
    )

    assignment = StudentFeeAssignment.objects.create(
        student=student,
        fee_plan=plan,
        start_date=date(2026, 1, 1)
    )

    TaxConfig.objects.create(name="GST", rate_basis_points=1800, is_active=True)

    return {
        "student": student,
        "plan": plan,
        "assignment": assignment,
        "admin": User.objects.create_user(username="admin_user_2", role=User.Role.ADMIN)
    }
