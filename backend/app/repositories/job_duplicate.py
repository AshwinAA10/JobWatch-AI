"""Repository for JobDuplicate entity persistence operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_duplicate import JobDuplicate, MatchType


class JobDuplicateRepository:
    """Data access repository for JobDuplicate records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        canonical_job_id: UUID,
        duplicate_job_id: UUID,
        match_type: str = MatchType.HIGH_CONFIDENCE.value,
        confidence_score: float = 1.0,
        matched_fields: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> JobDuplicate:
        """Create and persist a new JobDuplicate relationship."""
        duplicate_record = JobDuplicate(
            canonical_job_id=canonical_job_id,
            duplicate_job_id=duplicate_job_id,
            match_type=match_type,
            confidence_score=confidence_score,
            matched_fields=matched_fields,
            reason=reason,
        )
        self.db.add(duplicate_record)
        self.db.commit()
        self.db.refresh(duplicate_record)
        return duplicate_record

    def get_by_id(self, id: UUID) -> Optional[JobDuplicate]:
        """Fetch a JobDuplicate by its primary key UUID."""
        return self.db.get(JobDuplicate, id)

    def get_by_duplicate_id(self, duplicate_job_id: UUID) -> Optional[JobDuplicate]:
        """Find duplicate record by the duplicate job's UUID."""
        stmt = select(JobDuplicate).where(JobDuplicate.duplicate_job_id == duplicate_job_id)
        return self.db.scalars(stmt).first()

    def get_duplicates_for_canonical(self, canonical_job_id: UUID) -> List[JobDuplicate]:
        """Retrieve all duplicate records pointing to a specific canonical job."""
        stmt = (
            select(JobDuplicate)
            .where(JobDuplicate.canonical_job_id == canonical_job_id)
            .order_by(JobDuplicate.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_duplicates(
        self,
        skip: int = 0,
        limit: int = 50,
        canonical_id: Optional[UUID] = None,
    ) -> List[JobDuplicate]:
        """List historical duplicate relationships with pagination and optional filtering."""
        stmt = select(JobDuplicate)
        if canonical_id is not None:
            stmt = stmt.where(JobDuplicate.canonical_job_id == canonical_id)
        stmt = stmt.order_by(JobDuplicate.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
