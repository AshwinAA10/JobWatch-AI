"""MonitoringRun database entity."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.career_source import CareerSource


class MonitoringRunStatus(str, Enum):
    """Execution status of a monitoring run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MonitoringTriggerType(str, Enum):
    """Source or reason that triggered the monitoring run."""

    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"


class MonitoringRun(Base, TimestampMixin):
    """Represents an individual scheduled or manual execution of a career source check."""

    __tablename__ = "monitoring_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    career_source_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("career_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MonitoringRunStatus.PENDING.value,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MonitoringTriggerType.SCHEDULED.value,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    jobs_fetched: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    jobs_created: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    jobs_updated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    jobs_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Relationships
    career_source: Mapped["CareerSource"] = relationship(
        "CareerSource",
        back_populates="monitoring_runs",
    )

    __table_args__ = (
        Index("ix_monitoring_runs_source_started", "career_source_id", "started_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<MonitoringRun(id={self.id}, source_id={self.career_source_id}, "
            f"status='{self.status}', trigger='{self.trigger_type}')>"
        )
