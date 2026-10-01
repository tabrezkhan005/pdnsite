from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import Batch, ClassSession, Enrollment
from apps.accounts.models import GuardianProfile, StaffProfile, StudentProfile, User
from apps.attendance.models import LeaveRequest


@pytest.fixture
def permission_setup(setup_data):
    # Setup data provides one branch, one batch, one staff (teacher), one guardian, one student
    batch = setup_data["batch"]
    teacher = setup_data["staff"]
    guardian = setup_data["student"].guardian
    student = setup_data["student"]

    # Enroll student in batch
    Enrollment.objects.create(student=student, batch=batch, status=Enrollment.Status.ACTIVE)

    # Create session
    session = ClassSession.objects.create(
        batch=batch,
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(hours=1),
        mode=ClassSession.Mode.ONLINE,
        meeting_url="http://zoom.us/test1"
    )

    # Create another batch, another teacher, another student for cross-tenant checks
    other_teacher_user = User.objects.create_user(username="other_teacher", role=User.Role.STAFF)
    other_teacher = StaffProfile.objects.create(user=other_teacher_user, branch=setup_data["branch"], is_teacher=True)

    other_batch = Batch.objects.create(
        course=batch.course, level=batch.level, branch=setup_data["branch"],
        teacher=other_teacher, name="Other Batch", days_of_week=[1],
        start_time=batch.start_time, end_time=batch.end_time, capacity=10, mode=Batch.Mode.OFFLINE
    )

    other_guardian_user = User.objects.create_user(username="other_guardian", role=User.Role.GUARDIAN)
    other_guardian = GuardianProfile.objects.create(user=other_guardian_user)

    other_student = StudentProfile.objects.create(
        full_name="Other Student", guardian=other_guardian, branch=setup_data["branch"], student_id="PDN-TST-26-0002"
    )
    Enrollment.objects.create(student=other_student, batch=other_batch, status=Enrollment.Status.ACTIVE)

    other_session = ClassSession.objects.create(
        batch=other_batch, starts_at=timezone.now(), ends_at=timezone.now() + timedelta(hours=1), mode=ClassSession.Mode.ONLINE
    )

    admin_user = User.objects.create_user(username="admin", role=User.Role.ADMIN)

    leave = LeaveRequest.objects.create(
        student=student, session=session, from_date=timezone.now().date(), to_date=timezone.now().date(), reason="Sick"
    )
    other_leave = LeaveRequest.objects.create(
        student=other_student, session=other_session, from_date=timezone.now().date(), to_date=timezone.now().date(), reason="Sick"
    )

    return {
        "admin": admin_user,
        "teacher": teacher.user,
        "other_teacher": other_teacher.user,
        "guardian": guardian.user,
        "other_guardian": other_guardian.user,
        "student": student,
        "student_user": student.user, # Might be None, let's create one
        "other_student": other_student,
        "session": session,
        "other_session": other_session,
        "leave": leave,
        "other_leave": other_leave
    }

@pytest.fixture
def with_student_users(permission_setup):
    su = User.objects.create_user(username="student", role=User.Role.STUDENT)
    permission_setup["student"].user = su
    permission_setup["student"].save()

    osu = User.objects.create_user(username="other_student", role=User.Role.STUDENT)
    permission_setup["other_student"].user = osu
    permission_setup["other_student"].save()

    permission_setup["student_user"] = su
    permission_setup["other_student_user"] = osu
    return permission_setup

@pytest.mark.django_db
def test_sessions_list_scoping(permission_setup):
    client = APIClient()
    url = reverse("session-list")

    # Unauthenticated
    assert client.get(url).status_code in [401, 403]

    # Admin sees all
    client.force_authenticate(user=permission_setup["admin"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 2

    # Teacher sees only their own
    client.force_authenticate(user=permission_setup["teacher"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 1
    assert results[0]["id"] == str(permission_setup["session"].id)

    # Other teacher sees their own
    client.force_authenticate(user=permission_setup["other_teacher"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 1
    assert results[0]["id"] == str(permission_setup["other_session"].id)

    # Guardian sees their child's sessions
    client.force_authenticate(user=permission_setup["guardian"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 1
    assert results[0]["id"] == str(permission_setup["session"].id)

@pytest.mark.django_db
def test_leave_request_scoping(permission_setup):
    client = APIClient()
    url = reverse("leave-list")

    # Admin sees all
    client.force_authenticate(user=permission_setup["admin"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 2

    # Teacher sees leaves for students in their batches
    client.force_authenticate(user=permission_setup["teacher"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 1
    assert results[0]["id"] == str(permission_setup["leave"].id)

    # Guardian sees their child's leaves
    client.force_authenticate(user=permission_setup["guardian"])
    data = client.get(url).data
    results = data.get("results", data)
    assert len(results) == 1
    assert results[0]["id"] == str(permission_setup["leave"].id)

@pytest.mark.django_db
def test_attendance_summary_scoping(with_student_users):
    client = APIClient()
    url = reverse("attendance-summary")
    data = {"student_id": str(with_student_users["student"].id)}
    other_data = {"student_id": str(with_student_users["other_student"].id)}

    # Guardian querying own child
    client.force_authenticate(user=with_student_users["guardian"])
    assert client.get(url, data).status_code == 200
    # Guardian querying other child -> 404
    assert client.get(url, other_data).status_code == 404

    # Student querying self
    client.force_authenticate(user=with_student_users["student_user"])
    # Uses self if no id provided
    assert client.get(url).status_code == 200
    # Student querying other child -> 404
    assert client.get(url, other_data).status_code == 404

    # Teacher querying their student
    client.force_authenticate(user=with_student_users["teacher"])
    assert client.get(url, data).status_code == 200
    # Teacher querying other student -> 404
    assert client.get(url, other_data).status_code == 404

@pytest.mark.django_db
def test_join_session_scoping(with_student_users):
    client = APIClient()
    session = with_student_users["session"]
    other_session = with_student_users["other_session"]

    url = reverse("session-join", args=[session.id])
    other_url = reverse("session-join", args=[other_session.id])

    # Student joins own session
    client.force_authenticate(user=with_student_users["student_user"])
    assert client.post(url).status_code == 200

    # Student joins other session -> ValueError mapping to 400 because they aren't enrolled
    # But wait, we want 400 or 404. Let's see what happens.
    # The view gets session (200), gets student (200), then calls join_session which raises ValueError "Not enrolled".
    assert client.post(other_url).status_code == 400

    # Guardian tries to join for their child
    client.force_authenticate(user=with_student_users["guardian"])
    assert client.post(url, {"student_id": str(with_student_users["student"].id)}).status_code == 200

    # Guardian tries to join for OTHER child -> 404 (due to scope_students)
    assert client.post(url, {"student_id": str(with_student_users["other_student"].id)}).status_code == 404
