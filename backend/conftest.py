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
