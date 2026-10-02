"""Reliability, Observability, and Production Hardening tests for Phase 11."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import redact_sensitive_str
from app.core.metrics import metrics


def test_request_id_generation_and_propagation(client: TestClient) -> None:
    """Verify that requests without X-Request-ID receive a generated one in header and response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert len(req_id) > 10


def test_request_id_preservation(client: TestClient) -> None:
    """Verify that an incoming valid X-Request-ID is preserved and echoed back."""
    custom_id = "test-custom-request-id-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_security_defensive_headers(client: TestClient) -> None:
    """Verify production security headers are attached to responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "")


def test_liveness_probe_endpoint(client: TestClient) -> None:
    """Verify GET /health/live returns 200 and process liveness metadata."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "JobWatch AI"


def test_readiness_probe_endpoint(client: TestClient, monkeypatch, test_engine) -> None:
    """Verify GET /health/ready checks database connection and reports readiness."""
    import app.core.database as db_mod

    monkeypatch.setattr(db_mod, "engine", test_engine)
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_metrics_telemetry_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/metrics returns aggregated telemetry metrics with bounded keys."""
    # Issue a few requests to record data
    client.get("/health")
    client.get("/health/live")

    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "http" in data
    assert "total_requests" in data["http"]
    assert data["http"]["total_requests"] > 0
    assert "requests_by_endpoint" in data["http"]


def test_sensitive_data_redaction() -> None:
    """Verify that tokens, passwords, and database credentials are redacted from logs."""
    raw_token_log = "User authenticated with Bearer eyJhbGciOiJIUzI1Ni.secret.signature"
    sanitized_token = redact_sensitive_str(raw_token_log)
    assert "[REDACTED_TOKEN]" in sanitized_token
    assert "eyJhbGciOiJIUzI1Ni" not in sanitized_token

    raw_pass_log = 'Payload contains password="SuperSecretPassword123!" inside'
    sanitized_pass = redact_sensitive_str(raw_pass_log)
    assert "[REDACTED_PASSWORD]" in sanitized_pass
    assert "SuperSecretPassword123!" not in sanitized_pass

    raw_db_log = "Connecting to postgresql+psycopg://jobwatch:mysecretpass@localhost:5432/jobwatch"
    sanitized_db = redact_sensitive_str(raw_db_log)
    assert "[REDACTED_DB_PASS]" in sanitized_db
    assert "mysecretpass" not in sanitized_db


def test_production_fail_fast_validation() -> None:
    """Verify that unsafe configurations cause an immediate startup failure in production mode."""
    # 1. Unsafe: DEBUG=True in production
    settings = Settings(
        APP_ENV="production",
        DEBUG=True,
        JWT_SECRET="long-custom-production-secret-key-1234567890",
        DATABASE_URL="postgresql+psycopg://prod_user:prod_pass@db.internal:5432/prod_db",
        CORS_ORIGINS=["https://jobwatch.ai"],
    )
    with pytest.raises(RuntimeError, match="DEBUG mode must be disabled in production"):
        settings.validate_production_configuration()

    # 2. Unsafe: default dev secret in production
    settings_bad_secret = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET="dev-insecure-jwt-secret-key-change-in-production-min32chars",
        DATABASE_URL="postgresql+psycopg://prod_user:prod_pass@db.internal:5432/prod_db",
        CORS_ORIGINS=["https://jobwatch.ai"],
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET must be at least 32 characters"):
        settings_bad_secret.validate_production_configuration()

    # 3. Safe production config succeeds cleanly
    settings_safe = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET="a-very-strong-production-jwt-secret-key-with-high-entropy-12345",
        DATABASE_URL="postgresql+psycopg://prod_user:secure_prod_pass@db.internal:5432/prod_db",
        CORS_ORIGINS=["https://jobwatch.ai"],
    )
    # Should not raise
    settings_safe.validate_production_configuration()


def test_auth_rate_limiting() -> None:
    """Verify rate limiter sliding window blocks requests exceeding limits."""
    from app.core.middleware import RateLimitMiddleware
    middleware = RateLimitMiddleware(app=None)
    key = "auth:192.168.1.100"
    max_requests = 5

    # First 5 attempts should succeed
    for _ in range(max_requests):
        allowed, _ = middleware._clean_and_check(key, max_requests=max_requests, window_seconds=60.0)
        assert allowed is True

    # 6th attempt within window must be rejected
    allowed, remaining = middleware._clean_and_check(key, max_requests=max_requests, window_seconds=60.0)
    assert allowed is False
    assert remaining == 0
