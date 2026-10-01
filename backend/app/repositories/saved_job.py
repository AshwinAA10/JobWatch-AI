"""Repository for SavedJob persistence, queries, and bookmark toggling."""

from datetime import datetime, timezone
import logging
from typing import List, Optional, Set, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.job import Job
from app.models.saved_job import SavedJob

logger = logging.getLogger(__name__)


class SavedJobRepository:
    """Data access repository for candidate saved/bookmarked jobs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_job(
        self,
        profile_id: UUID,
        job_id: UUID,
        notes: Optional[str] = None,
    ) -> SavedJob:
        """Bookmark a job for a candidate profile (idempotent)."""
        existing = self.get_by_profile_and_job(profile_id, job_id)
        if existing:
            if notes is not None:
                existing.notes = notes
                self.db.commit()
                self.db.refresh(existing)
            return existing

        saved = SavedJob(
            profile_id=profile_id,
            job_id=job_id,
            notes=notes,
        )
        self.db.add(saved)
        self.db.commit()
        self.db.refresh(saved)
        return saved

    def unsave_job(self, profile_id: UUID, job_id: UUID) -> bool:
        """Remove a bookmark for a candidate profile."""
        saved = self.get_by_profile_and_job(profile_id, job_id)
        if saved:
            self.db.delete(saved)
            self.db.commit()
            return True
        return False

    def is_saved(self, profile_id: UUID, job_id: UUID) -> bool:
        """Check if a job is saved by candidate."""
        stmt = select(func.count(SavedJob.id)).where(
            SavedJob.profile_id == profile_id,
            SavedJob.job_id == job_id,
        )
        return (self.db.scalar(stmt) or 0) > 0

    def get_saved_job_ids(self, profile_id: UUID) -> Set[UUID]:
        """Fetch all job IDs saved by a candidate for fast lookup."""
        stmt = select(SavedJob.job_id).where(SavedJob.profile_id == profile_id)
        return set(self.db.scalars(stmt).all())

    def get_by_profile_and_job(
        self,
        profile_id: UUID,
        job_id: UUID,
    ) -> Optional[SavedJob]:
        """Fetch saved job record by candidate and job."""
        stmt = select(SavedJob).where(
            SavedJob.profile_id == profile_id,
            SavedJob.job_id == job_id,
        )
        return self.db.scalars(stmt).first()

    def list_saved_for_profile(
        self,
        profile_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Job], int]:
        """List bookmarked Job entities for a candidate with pagination.

        Returns (jobs, total_count).
        """
        count_stmt = select(func.count(SavedJob.id)).where(SavedJob.profile_id == profile_id)
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Job)
            .join(SavedJob, SavedJob.job_id == Job.id)
            .where(SavedJob.profile_id == profile_id)
            .options(selectinload(Job.company), selectinload(Job.career_source))
            .order_by(SavedJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = list(self.db.scalars(stmt).all())
        return jobs, total
