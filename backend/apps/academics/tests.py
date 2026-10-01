import pytest
from datetime import date, time, datetime
from django.utils import timezone
from apps.academics.models import Course, Branch, Level, Batch, Holiday, ClassSession, Enrollment
from apps.accounts.models import StaffProfile, StudentProfile, GuardianProfile, User
from apps.academics.services import generate_sessions, enroll_student

@pytest.fixture
def setup_data():
    branch = Branch.objects.create(name="Test Branch", slug="test", code="TST", address="Test")
    course = Course.objects.create(title="Test Course", slug="test-course", duration="1 year")
    level = Level.objects.create(course=course, name="Beginner")
    
    user_staff = User.objects.create_user(username="teacher", role=User.Role.STAFF)
    staff = StaffProfile.objects.create(user=user_staff, branch=branch, is_teacher=True)
    
    user_guardian = User.objects.create_user(username="guardian", role=User.Role.GUARDIAN)
    guardian = GuardianProfile.objects.create(user=user_guardian)
    
    student = StudentProfile.objects.create(
        full_name="Test Student", 
        guardian=guardian, 
        branch=branch,
        student_id="PDN-TST-26-0001"
    )
    
    batch = Batch.objects.create(
        course=course,
        level=level,
        branch=branch,
        teacher=staff,
        name="Test Batch",
        days_of_week=[0, 2], # Monday, Wednesday
        start_time=time(17, 0),
        end_time=time(18, 0),
        capacity=1,
        mode=Batch.Mode.OFFLINE
    )
    
    return {
        "branch": branch,
        "batch": batch,
        "student": student,
        "staff": staff
    }

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
