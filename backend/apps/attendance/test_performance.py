from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import ClassSession, Enrollment
from apps.accounts.models import User
from apps.attendance.models import LeaveRequest


@pytest.fixture
def perf_setup(setup_data):
    admin = User.objects.create_superuser(username="admin_perf", password="pwd", email="admin2@example.com", role=User.Role.ADMIN)

    # Create multiple sessions, leaves, etc.
    batch = setup_data["batch"]
    student = setup_data["student"]

    Enrollment.objects.create(student=student, batch=batch, status=Enrollment.Status.ACTIVE)

    for i in range(10):
        ClassSession.objects.create(
            batch=batch,
            starts_at=timezone.now() + timedelta(days=i),
            ends_at=timezone.now() + timedelta(days=i, hours=1),
            mode=ClassSession.Mode.ONLINE
        )
        LeaveRequest.objects.create(
            student=student,
            from_date=timezone.now().date() + timedelta(days=i),
            to_date=timezone.now().date() + timedelta(days=i),
            reason=f"Reason {i}"
        )
    return {"admin": admin, "student": student, "batch": batch}

@pytest.mark.django_db
def test_sessions_list_nplus1(perf_setup, django_assert_max_num_queries):
    client = APIClient()
    client.force_authenticate(user=perf_setup["admin"])

    url = reverse("session-list")

    # Pre-fetch or select_related check
    # Without select_related, it might do 10 queries. We expect a constant low number.
    with django_assert_max_num_queries(5):
        resp = client.get(url)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 10

@pytest.mark.django_db
def test_leaves_list_nplus1(perf_setup, django_assert_max_num_queries):
    client = APIClient()
    client.force_authenticate(user=perf_setup["admin"])

    url = reverse("leave-list")

    with django_assert_max_num_queries(5):
        resp = client.get(url)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 10
