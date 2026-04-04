"""API endpoint tests."""

import os
import pytest

# Ensure API_KEY is set before importing app
os.environ.setdefault("API_KEY", "test-api-key")

from fastapi.testclient import TestClient
from app.main import app

AUTH_HEADER = {"Authorization": "Bearer test-api-key"}


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_status(self, client):
        resp = client.get("/api/v1/health")
        # May be 200 or 503 depending on Redis availability
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert data["status"] in ("ok", "degraded")


class TestReadingEndpoint:
    def test_reading_requires_auth(self, client):
        resp = client.post("/api/v1/reading", json={
            "full_name": "Test User",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_city": "Mumbai",
            "birth_country": "India",
        })
        assert resp.status_code in (401, 403)

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
            headers=AUTH_HEADER,
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
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 422

    def test_reading_rejects_wrong_api_key(self, client):
        resp = client.post(
            "/api/v1/reading",
            json={
                "full_name": "Test User",
                "birth_date": "1990-06-15",
                "birth_time": "14:30",
                "birth_city": "Mumbai",
                "birth_country": "India",
            },
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401


class TestChartEndpoint:
    def test_chart_requires_auth(self, client):
        resp = client.post("/api/v1/chart", json={
            "full_name": "Test User",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_city": "Mumbai",
            "birth_country": "India",
        })
        assert resp.status_code in (401, 403)


class TestReadingRetrieval:
    def test_get_nonexistent_reading(self, client):
        resp = client.get(
            "/api/v1/reading/00000000-0000-0000-0000-000000000000",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 404

    def test_get_reading_requires_auth(self, client):
        resp = client.get("/api/v1/reading/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403)


class TestAdminEndpoints:
    def test_llm_status_returns_providers(self, client):
        resp = client.get("/admin/llm/status", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert "providers" in resp.json()

    def test_llm_status_requires_auth(self, client):
        resp = client.get("/admin/llm/status")
        assert resp.status_code in (401, 403)
