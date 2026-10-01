"""
Root conftest for pytest-django.

Sets up environment variables before Django loads so tests can run
without a .env file (e.g. in CI).
"""

import os

import django


def pytest_configure():
    """Set test-safe defaults before Django loads settings."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
    os.environ.setdefault("DATABASE_URL", "postgres://pdn:pdn@localhost:5432/pdn_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
    os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")

    django.setup()

# ruff: noqa: E402

from datetime import time

import pytest

from apps.academics.models import Batch, Branch, Course, Level
from apps.accounts.models import GuardianProfile, StaffProfile, StudentProfile, User


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
        days_of_week=[0, 2],
        start_time=time(17, 0),
        end_time=time(18, 0),
        capacity=1,
        mode=Batch.Mode.OFFLINE
    )

    return {
        "branch": branch,
        "batch": batch,
        "student": student,
        "staff": staff,
        "course": course
    }
