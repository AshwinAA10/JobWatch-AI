"""Pydantic schemas for authentication and user management."""

from datetime import datetime
import re
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for user account registration."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        """Validate and lowercase normalize user email."""
        v = v.strip().lower()
        # Basic RFC 5322 regex validation
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        if len(v) > 255:
            raise ValueError("Email exceeds maximum length of 255 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate minimum length and presence of password."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password exceeds maximum allowed length of 128 characters")
        return v


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Lowercase and trim email for login."""
        return v.strip().lower()


class TokenResponse(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserResponse(BaseModel):
    """Public user identity schema (passwords strictly excluded)."""

    id: UUID
    email: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
