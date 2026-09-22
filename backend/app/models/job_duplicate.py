"""Job duplicate database entity for establishing cross-source canonical relationships."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job


class MatchType(str, Enum):
    """Classification of matching signals used to detect duplicates."""

    EXACT_EXTERNAL_ID = "EXACT_EXTERNAL_ID"
    EXACT_APPLICATION_URL = "EXACT_APPLICATION_URL"
    EXACT_SOURCE_URL = "EXACT_SOURCE_URL"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    MANUAL = "MANUAL"


class JobDuplicate(Base, TimestampMixin):
    """Represents a validated duplicate relationship between a canonical job and duplicate job."""

    __tablename__ = "job_duplicates"
    __table_args__ = (
        CheckConstraint(
            "canonical_job_id != duplicate_job_id",
            name="ck_job_duplicates_no_self_duplicate",
        ),
        UniqueConstraint(
            "duplicate_job_id",
            name="uq_job_duplicates_duplicate_job_id",
        ),
        Index("ix_job_duplicates_canonical_job_id", "canonical_job_id"),
        Index("ix_job_duplicates_duplicate_job_id", "duplicate_job_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    canonical_job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    duplicate_job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    match_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=MatchType.HIGH_CONFIDENCE.value,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    matched_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    canonical_job: Mapped["Job"] = relationship(
        "Job",
        foreign_keys=[canonical_job_id],
        back_populates="duplicate_records",
    )
    duplicate_job: Mapped["Job"] = relationship(
        "Job",
        foreign_keys=[duplicate_job_id],
    )

    def __repr__(self) -> str:
        return (
            f"<JobDuplicate(id={self.id}, canonical={self.canonical_job_id}, "
            f"duplicate={self.duplicate_job_id}, score={self.confidence_score}, "
            f"type='{self.match_type}')>"
        )
