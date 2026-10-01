"""CandidateEmbedding database entity capturing semantic vector representations of candidates."""

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
    from app.models.candidate_profile import CandidateProfile


class CandidateEmbedding(Base, TimestampMixin):
    """Vector embedding of a candidate's skills, background, and preferences."""

    __tablename__ = "candidate_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "content_hash",
            "model",
            "embedding_version",
            name="uq_candidate_embeddings_cache",
        ),
        Index("ix_candidate_embeddings_profile_id", "profile_id"),
        Index("ix_candidate_embeddings_content_hash", "content_hash"),
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

    # Relationship to CandidateProfile
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="embeddings",
    )

    def __repr__(self) -> str:
        return f"<CandidateEmbedding(profile_id={self.profile_id}, model='{self.model}', version='{self.embedding_version}')>"
