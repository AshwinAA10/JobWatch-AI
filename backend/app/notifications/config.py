"""Constants, status enums, and template versions for notifications."""

from enum import Enum


class NotificationType(str, Enum):
    """Supported business event notification types."""

    NEW_MATCH = "NEW_MATCH"
    HIGH_QUALITY_MATCH = "HIGH_QUALITY_MATCH"


class NotificationChannelType(str, Enum):
    """Supported dispatch channels."""

    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


class DeliveryStatus(str, Enum):
    """Delivery attempt status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NotificationStatus(str, Enum):
    """Overall notification aggregate status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


EMAIL_TEMPLATE_VERSION: str = "v1"
WEBHOOK_PAYLOAD_VERSION: str = "v1"
HIGH_QUALITY_MATCH_THRESHOLD: float = 85.0
