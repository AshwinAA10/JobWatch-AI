"""AIJobExtraction database entity capturing cached LLM-extracted job requirements."""

from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job


class AIJobExtraction(Base, TimestampMixin):
    """Persisted structured requirements extracted from raw job descriptions by LLM."""

    __tablename__ = "ai_job_extractions"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "input_hash",
            "model",
            "prompt_version",
            name="uq_ai_job_extractions_cache",
        ),
        Index("ix_ai_job_extractions_job_id", "job_id"),
        Index("ix_ai_job_extractions_input_hash", "input_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Cache & Lineage tracking
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
    extraction_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )

    # Structured requirements payload
    structured_requirements: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Operational metrics
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    duration_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="ai_extractions",
    )

    def __repr__(self) -> str:
        return f"<AIJobExtraction(job_id={self.job_id}, model='{self.model}', success={self.is_success})>"
