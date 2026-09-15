"""Tests for application health and status endpoints."""

from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient) -> None:
    """Verify that GET /health returns 200 and expected health metadata."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "JobWatch AI"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """Verify that GET /api/v1/health returns 200 matching schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "JobWatch AI"


def test_root_metadata_endpoint(client: TestClient) -> None:
    """Verify that GET / returns application metadata."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "operational"
    assert "Phase 0" in data["phase"]
