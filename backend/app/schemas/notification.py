"""Pydantic schemas for notifications, deliveries, and candidate preferences."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationPreferenceBase(BaseModel):
    """Base notification preference attributes."""

    email_enabled: bool = False
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    minimum_match_score: float = Field(75.0, ge=0.0, le=100.0)
    frequency: str = Field("IMMEDIATE", pattern="^(IMMEDIATE|DAILY_DIGEST)$")
    max_per_hour: int = Field(10, ge=1, le=100)


class NotificationPreferenceUpdate(BaseModel):
    """Payload to update candidate notification preferences."""

    email_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    minimum_match_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    frequency: Optional[str] = Field(None, pattern="^(IMMEDIATE|DAILY_DIGEST)$")
    max_per_hour: Optional[int] = Field(None, ge=1, le=100)


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Response representation of candidate notification preferences."""

    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("webhook_secret", mode="after")
    @classmethod
    def mask_secret(cls, v: Optional[str]) -> Optional[str]:
        """Never expose raw webhook secrets in API responses."""
        if v:
            return "********"
        return None


class NotificationDeliveryResponse(BaseModel):
    """Delivery attempt status across a specific channel."""

    id: UUID
    notification_id: UUID
    channel: str
    status: str
    attempt_count: int
    max_attempts: int
    provider_message_id: Optional[str] = None
    last_error: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    """Candidate notification item with delivery history."""

    id: UUID
    profile_id: UUID
    event_type: str
    job_id: UUID
    match_id: Optional[UUID] = None
    title: str
    body: str
    status: str
    is_read: bool
    read_at: Optional[datetime] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    deliveries: List[NotificationDeliveryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of candidate notifications."""

    items: List[NotificationResponse]
    total: int
    skip: int
    limit: int
    unread_count: int
