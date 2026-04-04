"""API endpoint tests."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestReadingEndpoint:
    def test_reading_requires_auth(self, client):
        resp = client.post("/api/v1/reading", json={
            "full_name": "Test User",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_city": "Mumbai",
            "birth_country": "India",
        })
        assert resp.status_code == 403  # no auth header

    def test_reading_rejects_invalid_name(self, client):
        resp = client.post(
            "/api/v1/reading",
            json={
                "full_name": "Test <script>alert(1)</script>",
                "birth_date": "1990-06-15",
                "birth_time": "14:30",
                "birth_city": "Mumbai",
                "birth_country": "India",
            },
            headers={"Authorization": "Bearer dev-api-key"},
        )
        assert resp.status_code == 422

    def test_reading_rejects_future_date(self, client):
        resp = client.post(
            "/api/v1/reading",
            json={
                "full_name": "Test User",
                "birth_date": "2099-01-01",
                "birth_time": "14:30",
                "birth_city": "Mumbai",
                "birth_country": "India",
            },
            headers={"Authorization": "Bearer dev-api-key"},
        )
        assert resp.status_code == 422


class TestChartEndpoint:
    def test_chart_requires_auth(self, client):
        resp = client.post("/api/v1/chart", json={
            "full_name": "Test User",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_city": "Mumbai",
            "birth_country": "India",
        })
        assert resp.status_code == 403


class TestReadingRetrieval:
    def test_get_nonexistent_reading(self, client):
        resp = client.get("/api/v1/reading/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
