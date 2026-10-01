import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from apps.attendance.models import Attendance, LeaveRequest, SessionJoin
from apps.academics.models import ClassSession, Enrollment, Batch
from apps.attendance.services import join_session, get_attendance_summary, approve_leave
from apps.academics.services import generate_sessions, enroll_student
from apps.accounts.models import User

@pytest.fixture
def attendance_setup(setup_data):
    # From academics tests setup_data: branch, batch, student, staff
    batch = setup_data["batch"]
    student = setup_data["student"]
    staff = setup_data["staff"]
    
    # Enroll student
    enroll_student(student, batch, staff.user)
    
    # Create a session happening right now
    now = timezone.now()
    session = ClassSession.objects.create(
        batch=batch,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        mode=ClassSession.Mode.ONLINE,
        meeting_url="http://zoom.us/test"
    )
    
    return {
        **setup_data,
        "session": session,
        "now": now
    }

@pytest.mark.django_db
def test_join_window_and_non_downgrade(attendance_setup):
    session = attendance_setup["session"]
    student = attendance_setup["student"]
    staff = attendance_setup["staff"]
    
    # Shift time to before window
    session.starts_at = timezone.now() + timedelta(minutes=20)
    session.ends_at = session.starts_at + timedelta(hours=1)
    session.save()
    
    with pytest.raises(ValueError, match="not yet open"):
        join_session(session, student, "127.0.0.1", "test", student.user)
        
    # Shift time to valid window (started 5 mins ago)
    session.starts_at = timezone.now() - timedelta(minutes=5)
    session.ends_at = session.starts_at + timedelta(hours=1)
    session.save()
    
    url = join_session(session, student, "127.0.0.1", "test", student.user)
    assert url == "http://zoom.us/test"
    
    att = Attendance.objects.get(session=session, student=student)
    assert att.status == Attendance.Status.PRESENT
    assert att.source == Attendance.Source.ONLINE_JOIN
    
    # Test non-downgrade (Teacher marked ABSENT, student joins -> PRESENT)
    att.status = Attendance.Status.ABSENT
    att.source = Attendance.Source.MANUAL
    att.save()
    
    join_session(session, student, "127.0.0.1", "test2", student.user)
    att.refresh_from_db()
    assert att.status == Attendance.Status.PRESENT
    assert att.source == Attendance.Source.ONLINE_JOIN

@pytest.mark.django_db
def test_leave_approval(attendance_setup):
    student = attendance_setup["student"]
    session = attendance_setup["session"]
    staff = attendance_setup["staff"]
    
    # Create leave request
    leave = LeaveRequest.objects.create(
        student=student,
        from_date=session.starts_at.date(),
        to_date=session.starts_at.date(),
        reason="Sick",
        requested_by=student.user
    )
    
    approve_leave(leave, staff.user)
    
    leave.refresh_from_db()
    assert leave.status == LeaveRequest.Status.APPROVED
    
    att = Attendance.objects.get(session=session, student=student)
    assert att.status == Attendance.Status.EXCUSED

@pytest.mark.django_db
def test_attendance_summary(attendance_setup):
    student = attendance_setup["student"]
    session = attendance_setup["session"]
    batch = attendance_setup["batch"]
    
    # Complete the session
    session.status = ClassSession.Status.COMPLETED
    session.save()
    
    # Mark present
    Attendance.objects.create(
        session=session,
        student=student,
        status=Attendance.Status.PRESENT,
        source=Attendance.Source.MANUAL
    )
    
    summary = get_attendance_summary(student, batch)
    assert summary["percentage"] == 100.0
    assert summary["present"] == 1
    assert summary["total"] == 1

@pytest.mark.django_db
def test_bulk_mark_api(attendance_setup):
    client = APIClient()
    staff = attendance_setup["staff"]
    session = attendance_setup["session"]
    student = attendance_setup["student"]
    
    client.force_authenticate(user=staff.user)
    
    url = reverse("session-bulk-mark", args=[session.id])
    data = {
        "attendances": [
            {"student_id": student.id, "status": "PRESENT", "note": "Good"}
        ]
    }
    
    resp = client.post(url, data, format="json")
    assert resp.status_code == 200
    
    att = Attendance.objects.get(session=session, student=student)
    assert att.status == Attendance.Status.PRESENT
    assert att.note == "Good"
