"""SavedJob entity representing bookmarked jobs by candidate profiles."""

from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.job import Job


class SavedJob(Base, TimestampMixin):
    """Represents a bookmarked or saved job opening for a candidate."""

    __tablename__ = "saved_jobs"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "job_id",
            name="uq_saved_jobs_profile_job",
        ),
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
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="saved_jobs",
    )
    job: Mapped["Job"] = relationship(
        "Job",
    )

    def __repr__(self) -> str:
        return f"<SavedJob(id={self.id}, profile_id={self.profile_id}, job_id={self.job_id})>"
