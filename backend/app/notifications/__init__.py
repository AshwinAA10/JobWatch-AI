"""Multi-channel notification dispatch layer.

Manages candidate alerts via email and webhooks with atomic claiming,
exponential backoff retries, and candidate preference filtering.
"""

from app.notifications.config import (
    DeliveryStatus,
    HIGH_QUALITY_MATCH_THRESHOLD,
    NotificationChannelType,
    NotificationStatus,
    NotificationType,
)
from app.notifications.exceptions import (
    DeliveryError,
    NotificationError,
    PermanentDeliveryError,
    RateLimitExceededError,
    SSRFSecurityError,
    TransientDeliveryError,
)
from app.notifications.payload import DeliveryResult, NotificationPayload
from app.notifications.service import NotificationService
from app.notifications.worker import NotificationDeliveryWorker

__all__ = [
    "NotificationType",
    "NotificationChannelType",
    "DeliveryStatus",
    "NotificationStatus",
    "HIGH_QUALITY_MATCH_THRESHOLD",
    "NotificationError",
    "DeliveryError",
    "TransientDeliveryError",
    "PermanentDeliveryError",
    "SSRFSecurityError",
    "RateLimitExceededError",
    "NotificationPayload",
    "DeliveryResult",
    "NotificationService",
    "NotificationDeliveryWorker",
]
