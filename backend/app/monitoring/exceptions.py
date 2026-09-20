"""Exceptions for the Monitoring Engine."""

from typing import Optional
from uuid import UUID


class MonitoringError(Exception):
    """Base exception for all monitoring domain errors."""

    def __init__(self, message: str, source_id: Optional[UUID] = None) -> None:
        super().__init__(message)
        self.message = message
        self.source_id = source_id

    def __str__(self) -> str:
        prefix = f"[Source {self.source_id}] " if self.source_id else ""
        return f"{prefix}{self.message}"


class SourceAlreadyRunningError(MonitoringError):
    """Raised when an execution is triggered for a career source that is already RUNNING."""
    pass


class SourceInactiveError(MonitoringError):
    """Raised when monitoring is attempted on a deactivated CareerSource."""
    pass


class SourceNotFoundError(MonitoringError):
    """Raised when the specified CareerSource does not exist in the database."""
    pass


class MonitoringExecutionTimeoutError(MonitoringError):
    """Raised when a monitoring execution exceeds the configured timeout."""
    pass
