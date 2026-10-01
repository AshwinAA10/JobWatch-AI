"""Data structures representing notification payloads and delivery results."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class NotificationPayload:
    """Standardized payload passed to notification channels for dispatch."""

    notification_id: UUID
    delivery_id: UUID
    profile_id: UUID
    event_type: str
    title: str
    body: str
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    job_data: Dict[str, Any] = field(default_factory=dict)
    match_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryResult:
    """Outcome of an attempted channel dispatch."""

    success: bool
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    is_transient: bool = False
    retry_after_seconds: Optional[float] = None
