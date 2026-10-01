"""Tests for candidate notification preferences API, defaults, and SSRF security."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def _get_auth_header(client: TestClient, email: str = "pref_user@example.com") -> dict:
    """Helper to register and login a user, returning Authorization header."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_default_preferences(client: TestClient):
    """Verify safe default preferences (notifications disabled by default, 75% threshold)."""
    headers = _get_auth_header(client, "default_prefs@example.com")

    res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["email_enabled"] is False
    assert data["webhook_enabled"] is False
    assert data["minimum_match_score"] == 75.0
    assert data["frequency"] == "IMMEDIATE"
    assert data["max_per_hour"] == 10
    assert data["webhook_url"] is None


def test_update_preferences_success(client: TestClient):
    """Verify updating preferences with valid settings."""
    headers = _get_auth_header(client, "update_prefs@example.com")

    update_payload = {
        "email_enabled": True,
        "webhook_enabled": True,
        "webhook_url": "https://example.com/webhooks/jobwatch",
        "webhook_secret": "my-secret-key-12345",
        "minimum_match_score": 82.5,
        "frequency": "DAILY_DIGEST",
        "max_per_hour": 15,
    }

    res = client.put("/api/v1/notifications/preferences", json=update_payload, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["email_enabled"] is True
    assert data["webhook_enabled"] is True
    assert data["webhook_url"] == "https://example.com/webhooks/jobwatch"
    # Verify raw secret is never exposed in response
    assert data["webhook_secret"] == "********"
    assert data["minimum_match_score"] == 82.5
    assert data["frequency"] == "DAILY_DIGEST"
    assert data["max_per_hour"] == 15


@pytest.mark.parametrize(
    "forbidden_url",
    [
        "http://localhost:8000/api",
        "http://127.0.0.1/webhook",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/alerts",
        "http://192.168.1.1/hook",
        "ftp://example.com/hook",
        "file:///etc/passwd",
        "javascript:alert(1)",
    ],
)
def test_webhook_url_ssrf_rejection(client: TestClient, forbidden_url: str):
    """Verify SSRF defense rejects loopback, private ranges, metadata IPs, and non-http schemes."""
    headers = _get_auth_header(client, f"ssrf_{abs(hash(forbidden_url))}@example.com")

    update_payload = {
        "webhook_enabled": True,
        "webhook_url": forbidden_url,
    }

    res = client.put("/api/v1/notifications/preferences", json=update_payload, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid webhook URL" in res.json()["detail"]


def test_unauthenticated_preferences_rejected(client: TestClient):
    """Verify anonymous access is rejected with 401 Unauthorized."""
    res = client.get("/api/v1/notifications/preferences")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
