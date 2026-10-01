"""JobEmbedding database entity capturing semantic vector representations of job postings."""

from typing import TYPE_CHECKING, List
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job


class JobEmbedding(Base, TimestampMixin):
    """Vector embedding of a job's structured and contextual representation."""

    __tablename__ = "job_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "content_hash",
            "model",
            "embedding_version",
            name="uq_job_embeddings_cache",
        ),
        Index("ix_job_embeddings_job_id", "job_id"),
        Index("ix_job_embeddings_content_hash", "content_hash"),
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

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    dimensions: Mapped[int] = mapped_column(
        Integer,
        default=1536,
        nullable=False,
    )
    embedding_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )

    # 1536-dimensional vector embedding
    embedding: Mapped[List[float]] = mapped_column(
        Vector(1536),
        nullable=False,
    )

    # Relationship to Job
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="embeddings",
    )

    def __repr__(self) -> str:
        return f"<JobEmbedding(job_id={self.job_id}, model='{self.model}', version='{self.embedding_version}')>"
