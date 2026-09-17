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
    assert "Phase 1" in data["phase"]


def test_api_v1_health_db_endpoint_success(client: TestClient, monkeypatch, test_engine) -> None:
    """Verify that GET /api/v1/health/db returns 200 when database is healthy."""
    import app.core.database as db_mod

    monkeypatch.setattr(db_mod, "engine", test_engine)
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "latency_ms" in data
    assert "timestamp" in data


def test_root_health_db_endpoint_success(client: TestClient, monkeypatch, test_engine) -> None:
    """Verify that GET /health/db returns 200 when database is healthy."""
    import app.core.database as db_mod

    monkeypatch.setattr(db_mod, "engine", test_engine)
    response = client.get("/health/db")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_db_endpoint_failure(client: TestClient, monkeypatch) -> None:
    """Verify that GET /api/v1/health/db returns 503 without leaking credentials on failure."""
    import app.core.database as db_mod

    monkeypatch.setattr(
        db_mod,
        "check_database_health",
        lambda: (False, 25.0, "Database connection failed"),
    )
    response = client.get("/api/v1/health/db")
    assert response.status_code == 503

    data = response.json()
    assert "detail" in data
    assert data["detail"]["status"] == "unhealthy"
    assert data["detail"]["database"] == "disconnected"
    # Ensure no credentials or stack traces appear
    assert "password" not in str(data).lower()
    assert "traceback" not in str(data).lower()
