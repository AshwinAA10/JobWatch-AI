"""Exception classes for notification dispatch, delivery, and security."""


class NotificationError(Exception):
    """Base exception for all notification-related errors."""
    pass


class DeliveryError(NotificationError):
    """Base exception for channel delivery failures."""

    def __init__(self, message: str, is_transient: bool = False, retry_after: float = None) -> None:
        super().__init__(message)
        self.is_transient = is_transient
        self.retry_after = retry_after


class TransientDeliveryError(DeliveryError):
    """Temporary delivery failure that should be retried (e.g. timeout, 429, 503)."""

    def __init__(self, message: str, retry_after: float = None) -> None:
        super().__init__(message, is_transient=True, retry_after=retry_after)


class PermanentDeliveryError(DeliveryError):
    """Permanent delivery failure that must not be retried (e.g. 400, auth failure, bad address)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, is_transient=False, retry_after=None)


class SSRFSecurityError(PermanentDeliveryError):
    """Raised when a webhook URL attempts to access private/internal network addresses."""
    pass


class RateLimitExceededError(NotificationError):
    """Raised when candidate notification hourly volume limit is exceeded."""
    pass
