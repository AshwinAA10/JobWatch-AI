"""JobMatch database entity capturing persisted matching results."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.job import Job
    from app.models.user import User


class JobMatch(Base, TimestampMixin):
    """Persisted deterministic match evaluation between a CandidateProfile and a Job."""

    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "job_id",
            name="uq_job_matches_profile_job",
        ),
        Index("ix_job_matches_profile_score", "profile_id", "score"),
        Index("ix_job_matches_job_score", "job_id", "score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scoring metrics
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    scoring_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )

    # Detailed evaluation payload (JSON)
    breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    matched_criteria: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    missing_criteria: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    mismatches: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    reasons: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Execution timestamp
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="job_matches",
    )
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="matches",
    )

    def __repr__(self) -> str:
        return f"<JobMatch(profile_id={self.profile_id}, job_id={self.job_id}, score={self.score})>"
