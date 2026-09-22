"""Deduplication domain exception hierarchy."""

from uuid import UUID
from typing import Optional


class DeduplicationError(Exception):
    """Base exception for all deduplication errors."""

    def __init__(self, message: str, job_id: Optional[UUID] = None) -> None:
        super().__init__(message)
        self.message = message
        self.job_id = job_id


class CanonicalCycleError(DeduplicationError):
    """Raised when establishing a duplicate relationship would create a cyclical canonical graph."""
    pass


class SelfDuplicateError(DeduplicationError):
    """Raised when a job is evaluated as duplicate of itself."""
    pass


class JobNotFoundError(DeduplicationError):
    """Raised when a target job is not found in repository."""
    pass
