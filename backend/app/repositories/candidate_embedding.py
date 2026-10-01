"""Repository for CandidateEmbedding entity persistence operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_embedding import CandidateEmbedding


class CandidateEmbeddingRepository:
    """Data access repository for CandidateEmbedding records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_profile_id(self, profile_id: UUID) -> Optional[CandidateEmbedding]:
        """Fetch latest embedding for a candidate profile."""
        stmt = (
            select(CandidateEmbedding)
            .where(CandidateEmbedding.profile_id == profile_id)
            .order_by(CandidateEmbedding.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_cached(
        self,
        profile_id: UUID,
        content_hash: str,
        model: str,
        embedding_version: str,
    ) -> Optional[CandidateEmbedding]:
        """Fetch cached embedding matching exact content hash, model, and version."""
        stmt = select(CandidateEmbedding).where(
            CandidateEmbedding.profile_id == profile_id,
            CandidateEmbedding.content_hash == content_hash,
            CandidateEmbedding.model == model,
            CandidateEmbedding.embedding_version == embedding_version,
        )
        return self.db.scalars(stmt).first()

    def save_embedding(
        self,
        profile_id: UUID,
        content_hash: str,
        model: str,
        dimensions: int,
        embedding_version: str,
        embedding: List[float],
    ) -> CandidateEmbedding:
        """Create or update a CandidateEmbedding record."""
        existing = self.db.scalars(
            select(CandidateEmbedding).where(
                CandidateEmbedding.profile_id == profile_id,
                CandidateEmbedding.content_hash == content_hash,
                CandidateEmbedding.model == model,
                CandidateEmbedding.embedding_version == embedding_version,
            )
        ).first()

        if existing:
            existing.embedding = embedding
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = CandidateEmbedding(
            profile_id=profile_id,
            content_hash=content_hash,
            model=model,
            dimensions=dimensions,
            embedding_version=embedding_version,
            embedding=embedding,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
