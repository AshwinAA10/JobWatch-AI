"""Job database entity."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.career_source import CareerSource
    from app.models.company import Company
    from app.models.job_duplicate import JobDuplicate


class Job(Base, TimestampMixin):
    """Represents an individual job opening discovered from a career source."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint(
            "career_source_id",
            "external_id",
            name="uq_jobs_source_external_id",
        ),
        Index("ix_jobs_company_active", "company_id", "is_active"),
        CheckConstraint(
            "canonical_job_id != id",
            name="ck_jobs_no_self_canonical",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    career_source_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("career_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers & Metadata
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Location & Employment Classification
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )  # e.g., 'full-time', 'part-time', 'contract', 'internship'
    workplace_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )  # e.g., 'remote', 'hybrid', 'on-site'

    # URLs
    application_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )

    # Lifecycle Timestamps (timezone-aware UTC)
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Operational status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Deduplication & Canonical Job Identity (Phase 4)
    canonical_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="jobs",
    )
    career_source: Mapped["CareerSource"] = relationship(
        "CareerSource",
        back_populates="jobs",
    )
    canonical_job: Mapped[Optional["Job"]] = relationship(
        "Job",
        remote_side=[id],
        back_populates="duplicate_jobs",
        foreign_keys=[canonical_job_id],
    )
    duplicate_jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="canonical_job",
        foreign_keys=[canonical_job_id],
    )
    duplicate_records: Mapped[List["JobDuplicate"]] = relationship(
        "JobDuplicate",
        foreign_keys="JobDuplicate.canonical_job_id",
        back_populates="canonical_job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title='{self.title}', external_id='{self.external_id}')>"
