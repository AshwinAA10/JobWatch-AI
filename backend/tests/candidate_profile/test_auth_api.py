"""API integration tests for authentication endpoints (/register, /login, /me)."""

from datetime import timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User


def test_register_endpoint_success(client: TestClient):
    """Verify successful user registration returns 201 and public user data without password."""
    payload = {
        "email": "NewUser@Example.COM  ",
        "password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_endpoint_duplicate_email(client: TestClient):
    """Verify duplicate email registration returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "ValidPassword123!",
    }
    client.post("/api/v1/auth/register", json=payload)

    # Second registration attempt
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


def test_register_endpoint_validation(client: TestClient):
    """Verify invalid email format and weak passwords are rejected."""
    # Invalid email
    res1 = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "ValidPassword123!"},
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Password too short (< 8 chars)
    res2 = client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_endpoint_success(client: TestClient):
    """Verify successful login returns signed JWT access token."""
    email = "login_user@example.com"
    password = "CorrectPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == status.HTTP_200_OK

    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] > 0


def test_login_endpoint_invalid_credentials(client: TestClient):
    """Verify incorrect password or non-existent user returns 401."""
    email = "test_invalid@example.com"
    password = "CorrectPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})

    # Wrong password
    res1 = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert res1.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid email or password" in res1.json()["detail"].lower()

    # Unknown email
    res2 = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": password},
    )
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_endpoint_authenticated(client: TestClient):
    """Verify /me endpoint returns authenticated user identity."""
    email = "me_user@example.com"
    password = "CorrectPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == status.HTTP_200_OK
    data = me_res.json()
    assert data["email"] == email
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_endpoint_unauthorized(client: TestClient):
    """Verify /me endpoint rejects requests with missing or invalid tokens."""
    # Missing token
    res1 = client.get("/api/v1/auth/me")
    assert res1.status_code == status.HTTP_401_UNAUTHORIZED

    # Invalid token format
    res2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED
