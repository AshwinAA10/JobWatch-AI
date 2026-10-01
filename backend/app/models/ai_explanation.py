"""AIExplanation database entity capturing persisted LLM-generated match explanations."""

from typing import TYPE_CHECKING, List
import uuid
from sqlalchemy import (
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
    from app.models.candidate_profile import CandidateProfile
    from app.models.job import Job


class AIExplanation(Base, TimestampMixin):
    """Persisted LLM-generated narrative explanation of candidate-job match evaluation."""

    __tablename__ = "ai_explanations"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "job_id",
            "input_hash",
            "model",
            "prompt_version",
            name="uq_ai_explanations_cache",
        ),
        Index("ix_ai_explanations_profile_id", "profile_id"),
        Index("ix_ai_explanations_job_id", "job_id"),
        Index("ix_ai_explanations_input_hash", "input_hash"),
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
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    input_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )
    explanation_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )

    # Narrative explanation content
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    strengths: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    gaps: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Relationships
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="ai_explanations",
    )
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="ai_explanations",
    )

    def __repr__(self) -> str:
        return f"<AIExplanation(profile_id={self.profile_id}, job_id={self.job_id}, model='{self.model}')>"
