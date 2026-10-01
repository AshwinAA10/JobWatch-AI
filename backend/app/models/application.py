"""Application database entity representing a candidate job application and its lifecycle."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.application_history import ApplicationHistory
    from app.models.application_note import ApplicationNote
    from app.models.candidate_profile import CandidateProfile
    from app.models.interview import Interview
    from app.models.job import Job


class Application(Base, TimestampMixin):
    """Represents a job application submitted by a candidate."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "job_id",
            name="uq_applications_profile_job",
        ),
        Index("ix_applications_profile_id", "profile_id"),
        Index("ix_applications_job_id", "job_id"),
        Index("ix_applications_status", "status"),
        Index("ix_applications_applied_at", "applied_at"),
        Index("ix_applications_last_status_changed_at", "last_status_changed_at"),
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
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default=ApplicationStatus.APPLIED.value,
        nullable=False,
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Snapshot fields preserving job context even if source job changes/inactivates
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    job_title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    job_location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    external_application_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    match_score_at_application: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="applications",
    )
    job: Mapped[Optional["Job"]] = relationship(
        "Job",
    )
    history: Mapped[List["ApplicationHistory"]] = relationship(
        "ApplicationHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationHistory.changed_at.desc()",
    )
    application_notes: Mapped[List["ApplicationNote"]] = relationship(
        "ApplicationNote",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationNote.created_at.desc()",
    )
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Interview.scheduled_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, profile_id={self.profile_id}, title='{self.job_title}', status='{self.status}')>"
