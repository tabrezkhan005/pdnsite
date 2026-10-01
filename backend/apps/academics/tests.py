from datetime import date, time

import pytest
from django.utils import timezone

from apps.academics.models import ClassSession, Enrollment, Holiday
from apps.academics.services import enroll_student, generate_sessions
from apps.accounts.models import StudentProfile


@pytest.mark.django_db
def test_generate_sessions_idempotency_and_holidays(setup_data):
    batch = setup_data["batch"]
    branch = setup_data["branch"]

    # 2026-10-05 is a Monday
    from_date = date(2026, 10, 5)
    to_date = date(2026, 10, 11) # Sun

    # Create holiday on Wednesday
    Holiday.objects.create(date=date(2026, 10, 7), branch=branch, reason="Festival")

    sessions = generate_sessions(batch, from_date, to_date)
    # Should only create 1 session (Monday) because Wednesday is a holiday
    assert len(sessions) == 1
    assert sessions[0].starts_at.weekday() == 0

    # Test timezone correctness
    assert sessions[0].starts_at.tzinfo == timezone.get_current_timezone()
    assert sessions[0].starts_at.time() == time(17, 0)

    # Test idempotency
    sessions_again = generate_sessions(batch, from_date, to_date)
    assert len(sessions_again) == 0
    assert ClassSession.objects.filter(batch=batch).count() == 1

@pytest.mark.django_db
def test_capacity_enforcement(setup_data):
    batch = setup_data["batch"]
    student = setup_data["student"]
    staff = setup_data["staff"]

    # Enroll first student (capacity is 1)
    enrollment1 = enroll_student(student, batch, staff.user)
    assert enrollment1.status == Enrollment.Status.ACTIVE

    # Create second student
    student2 = StudentProfile.objects.create(
        full_name="Test Student 2",
        guardian=student.guardian,
        branch=student.branch,
        student_id="PDN-TST-26-0002"
    )

    # Attempt to enroll second student should fail
    with pytest.raises(ValueError, match="is full"):
        enroll_student(student2, batch, staff.user)
