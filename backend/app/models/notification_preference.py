"""Candidate notification preference database entity."""

from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile


class NotificationPreference(Base, TimestampMixin):
    """Candidate notification settings controlling channels, frequency, and score thresholds."""

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("profile_id", name="uq_notification_preferences_profile_id"),
        Index("ix_notification_preferences_profile_id", "profile_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Channel toggles
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Webhook endpoint configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    webhook_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Match thresholds and cadence
    minimum_match_score: Mapped[float] = mapped_column(
        Float,
        default=75.0,
        nullable=False,
    )
    frequency: Mapped[str] = mapped_column(
        String(32),
        default="IMMEDIATE",
        nullable=False,
    )
    max_per_hour: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # Relationship to CandidateProfile
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="notification_preference",
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationPreference(profile_id={self.profile_id}, "
            f"email_enabled={self.email_enabled}, webhook_enabled={self.webhook_enabled})>"
        )
