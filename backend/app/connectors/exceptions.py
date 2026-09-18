"""Connector-specific exception hierarchy."""

from typing import Optional


class ConnectorError(Exception):
    """Base exception for all connector-related failures."""

    def __init__(self, message: str, source_type: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.source_type = source_type

    def __str__(self) -> str:
        prefix = f"[{self.source_type}] " if self.source_type else ""
        return f"{prefix}{self.message}"


class ConnectorConfigurationError(ConnectorError):
    """Raised when a career source has missing or invalid configuration."""
    pass


class UnsupportedConnectorError(ConnectorConfigurationError):
    """Raised when an ingestion request specifies an unregistered source_type."""
    pass


class ConnectorRequestError(ConnectorError):
    """Raised when an HTTP transport or network-level error occurs."""
    pass


class ConnectorRateLimitError(ConnectorRequestError):
    """Raised when the external provider throttles requests (HTTP 429)."""

    def __init__(
        self,
        message: str,
        source_type: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, source_type=source_type)
        self.status_code = 429
        self.retry_after = retry_after


class ConnectorResponseError(ConnectorError):
    """Raised when the external provider returns an unhandled error status (4xx/5xx)."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        source_type: Optional[str] = None,
    ) -> None:
        super().__init__(message, source_type=source_type)
        self.status_code = status_code


class ConnectorParseError(ConnectorError):
    """Raised when provider payload fails schema validation or normalization."""
    pass
