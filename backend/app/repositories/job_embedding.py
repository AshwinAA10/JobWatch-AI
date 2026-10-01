"""Repository for JobEmbedding entity persistence operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_embedding import JobEmbedding


class JobEmbeddingRepository:
    """Data access repository for JobEmbedding records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(self, job_id: UUID) -> Optional[JobEmbedding]:
        """Fetch latest embedding for a job."""
        stmt = (
            select(JobEmbedding)
            .where(JobEmbedding.job_id == job_id)
            .order_by(JobEmbedding.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_cached(
        self,
        job_id: UUID,
        content_hash: str,
        model: str,
        embedding_version: str,
    ) -> Optional[JobEmbedding]:
        """Fetch cached embedding matching exact content hash, model, and version."""
        stmt = select(JobEmbedding).where(
            JobEmbedding.job_id == job_id,
            JobEmbedding.content_hash == content_hash,
            JobEmbedding.model == model,
            JobEmbedding.embedding_version == embedding_version,
        )
        return self.db.scalars(stmt).first()

    def save_embedding(
        self,
        job_id: UUID,
        content_hash: str,
        model: str,
        dimensions: int,
        embedding_version: str,
        embedding: List[float],
    ) -> JobEmbedding:
        """Create or update a JobEmbedding record."""
        existing = self.db.scalars(
            select(JobEmbedding).where(
                JobEmbedding.job_id == job_id,
                JobEmbedding.content_hash == content_hash,
                JobEmbedding.model == model,
                JobEmbedding.embedding_version == embedding_version,
            )
        ).first()

        if existing:
            existing.embedding = embedding
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = JobEmbedding(
            job_id=job_id,
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
