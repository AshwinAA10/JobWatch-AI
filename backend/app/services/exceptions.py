"""Domain exceptions for authentication, user profiles, and candidate services."""

from typing import Optional
from uuid import UUID


class DomainError(Exception):
    """Base exception for application domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthError(DomainError):
    """Base exception for authentication failures."""
    pass


class DuplicateEmailError(AuthError):
    """Raised when registering an email address that already exists."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when authentication credentials fail verification."""
    pass


class InactiveUserError(AuthError):
    """Raised when an inactive user attempts to authenticate."""
    pass


class TokenError(AuthError):
    """Raised when JWT token decoding, validation, or expiration fails."""
    pass


class ProfileError(DomainError):
    """Base exception for candidate profile operations."""
    pass


class ProfileNotFoundError(ProfileError):
    """Raised when a candidate profile cannot be found."""

    def __init__(self, user_id: Optional[UUID] = None) -> None:
        msg = f"Candidate profile not found for user {user_id}" if user_id else "Candidate profile not found"
        super().__init__(msg)
        self.user_id = user_id


class ResourceNotFoundError(ProfileError):
    """Raised when a child profile resource (skill, experience, education) is not found."""
    pass


class DuplicateSkillError(ProfileError):
    """Raised when attaching a skill that is already present on the profile."""
    pass


class UnauthorizedAccessError(DomainError):
    """Raised when attempting an unauthorized modification to a resource."""
    pass
