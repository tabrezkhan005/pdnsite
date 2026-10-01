"""Tests for the health-check endpoint."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestHealthEndpoint:
    """Verify the /health/ endpoint checks database connectivity."""

    def test_health_returns_ok(self, client: Client):
        """GET /health/ should return 200 with status=ok when DB is reachable."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

    def test_health_content_type(self, client: Client):
        """GET /health/ should return application/json."""
        response = client.get("/health/")
        assert response["Content-Type"] == "application/json"
