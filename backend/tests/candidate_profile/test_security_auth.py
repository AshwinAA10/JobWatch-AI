"""Unit tests for password security, JWT operations, and AuthService logic."""

from datetime import timedelta
import uuid
import pytest
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import UserRegisterRequest
from app.services.auth import AuthService
from app.services.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    TokenError,
)


def test_password_hashing_and_verification():
    """Verify that password hashing produces Argon2 hashes that verify correctly."""
    raw_password = "SuperSecretPassword123!"
    pw_hash = hash_password(raw_password)

    assert pw_hash != raw_password
    assert pw_hash.startswith("$argon2")
    assert verify_password(raw_password, pw_hash) is True
    assert verify_password("WrongPassword!", pw_hash) is False
    assert verify_password("", pw_hash) is False
    assert verify_password(raw_password, "invalid_hash_string") is False


def test_password_hash_empty_fails():
    """Verify that empty passwords cannot be hashed."""
    with pytest.raises(ValueError):
        hash_password("")


def test_jwt_token_lifecycle():
    """Verify standard creation and decoding of JWT access tokens."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_token_expiration():
    """Verify that expired tokens raise ExpiredSignatureError."""
    user_id = uuid.uuid4()
    # Expire 10 seconds ago
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(ExpiredSignatureError):
        decode_access_token(expired_token)


def test_jwt_token_invalid_signature():
    """Verify that tampered tokens fail validation."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)
    tampered = token[:-4] + "abcd"

    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_auth_service_register_and_authenticate(db_session: Session):
    """Verify full AuthService registration, authentication, and login flow."""
    auth_service = AuthService(db_session)
    email = "candidate@example.com"
    password = "SecurePassword123!"

    # Registration
    register_req = UserRegisterRequest(email=email, password=password)
    user = auth_service.register(register_req)
    assert user.id is not None
    assert user.email == email.lower()
    assert user.is_active is True
    assert user.password_hash != password

    # Duplicate registration fails
    with pytest.raises(DuplicateEmailError):
        auth_service.register(register_req)

    # Authentication success
    authenticated = auth_service.authenticate(email, password)
    assert authenticated.id == user.id
    assert authenticated.last_login_at is not None

    # Authentication failure - wrong password
    with pytest.raises(InvalidCredentialsError):
        auth_service.authenticate(email, "WrongPassword!")

    # Authentication failure - unknown email
    with pytest.raises(InvalidCredentialsError):
        auth_service.authenticate("unknown@example.com", password)


def test_auth_service_inactive_user(db_session: Session):
    """Verify that disabled/inactive user accounts are rejected."""
    auth_service = AuthService(db_session)
    email = "inactive@example.com"
    password = "SecurePassword123!"

    user = auth_service.register(UserRegisterRequest(email=email, password=password))
    user.is_active = False
    db_session.add(user)
    db_session.commit()

    with pytest.raises(InactiveUserError):
        auth_service.authenticate(email, password)

    # Token resolution also rejects inactive users
    token = create_access_token(subject=user.id)
    with pytest.raises(InactiveUserError):
        auth_service.get_user_from_token(token)


def test_auth_service_invalid_token(db_session: Session):
    """Verify token resolution with expired or invalid tokens raises TokenError."""
    auth_service = AuthService(db_session)

    with pytest.raises(TokenError):
        auth_service.get_user_from_token("not-a-valid-token")

    # Non-existent user id in token
    non_existent_token = create_access_token(subject=uuid.uuid4())
    with pytest.raises(TokenError):
        auth_service.get_user_from_token(non_existent_token)
