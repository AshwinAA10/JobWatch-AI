"""Interview entity tracking scheduled and completed candidate interview stages."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.enums import InterviewStatus, InterviewType

if TYPE_CHECKING:
    from app.models.application import Application


class Interview(Base, TimestampMixin):
    """Represents an interview round scheduled for a candidate's application."""

    __tablename__ = "interviews"
    __table_args__ = (
        Index("ix_interviews_application_id", "application_id"),
        Index("ix_interviews_scheduled_at", "scheduled_at"),
        Index("ix_interviews_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    interview_type: Mapped[str] = mapped_column(
        String(32),
        default=InterviewType.TECHNICAL.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=InterviewStatus.SCHEDULED.value,
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    interviewer_names: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    meeting_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="interviews",
    )

    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, application_id={self.application_id}, type='{self.interview_type}', status='{self.status}')>"
