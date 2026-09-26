"""Service handling user registration, authentication, and JWT lifecycle."""

from typing import Optional
from uuid import UUID
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse, UserRegisterRequest
from app.services.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    TokenError,
)


class AuthService:
    """Service encapsulating user identity, credential validation, and JWT sessions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

    def register(self, register_in: UserRegisterRequest) -> User:
        """Register a new user account with hashed password.

        Args:
            register_in: Validated registration payload.

        Returns:
            Newly created User entity.

        Raises:
            DuplicateEmailError: If an account already exists with the given email.
        """
        existing = self.user_repo.get_by_email(register_in.email)
        if existing:
            raise DuplicateEmailError("An account with this email already exists")

        pw_hash = hash_password(register_in.password)
        user = self.user_repo.create(
            email=register_in.email,
            password_hash=pw_hash,
            is_active=True,
            is_verified=False,
        )
        return user

    def authenticate(self, email: str, password: str) -> User:
        """Authenticate user credentials and update login timestamp.

        Args:
            email: User email.
            password: User plaintext password.

        Returns:
            Authenticated User entity.

        Raises:
            InvalidCredentialsError: If credentials do not match any active user.
            InactiveUserError: If user account has been disabled.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        user = self.user_repo.update_last_login(user)
        return user

    def create_token_response(self, user: User) -> TokenResponse:
        """Issue a signed JWT access token for an authenticated user."""
        token = create_access_token(subject=user.id)
        expires_seconds = self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=expires_seconds,
        )

    def get_user_from_token(self, token: str) -> User:
        """Validate an access token and return the associated active user.

        Args:
            token: Raw JWT bearer token.

        Returns:
            Active User entity.

        Raises:
            TokenError: If token is expired, malformed, or references a non-existent or inactive user.
        """
        try:
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if not sub:
                raise TokenError("Token missing subject identifier")
            user_id = UUID(sub)
        except ExpiredSignatureError:
            raise TokenError("Access token has expired")
        except (InvalidTokenError, ValueError) as exc:
            raise TokenError(f"Invalid access token: {str(exc)}")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise TokenError("User associated with token does not exist")
        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        return user
