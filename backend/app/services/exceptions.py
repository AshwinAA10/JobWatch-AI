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


class MatchingError(DomainError):
    """Base exception for matching engine errors."""
    pass


class JobNotFoundError(MatchingError):
    """Raised when a job target cannot be found."""

    def __init__(self, job_id: Optional[UUID] = None) -> None:
        msg = f"Job not found for ID {job_id}" if job_id else "Job not found"
        super().__init__(msg)
        self.job_id = job_id


class ApplicationError(DomainError):
    """Base exception for application tracking lifecycle errors."""
    pass


class ApplicationNotFoundError(ApplicationError):
    """Raised when an application is not found or does not belong to the candidate."""

    def __init__(self, application_id: Optional[UUID] = None) -> None:
        msg = f"Application not found for ID {application_id}" if application_id else "Application not found"
        super().__init__(msg)
        self.application_id = application_id


class DuplicateApplicationError(ApplicationError):
    """Raised when an application for the specified job already exists for the candidate."""
    pass


class InvalidStatusTransitionError(ApplicationError):
    """Raised when a requested status transition is not permitted."""
    pass


class InterviewNotFoundError(ApplicationError):
    """Raised when an interview record is not found."""
    pass

