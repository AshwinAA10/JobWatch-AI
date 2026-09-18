"""Repository for Job data access operations."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


class JobRepository:
    """Data access repository for Job entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, job_in: JobCreate) -> Job:
        """Create and persist a new Job opening."""
        job = Job(
            company_id=job_in.company_id,
            career_source_id=job_in.career_source_id,
            external_id=job_in.external_id,
            title=job_in.title,
            description=job_in.description,
            location=job_in.location,
            employment_type=job_in.employment_type,
            workplace_type=job_in.workplace_type,
            application_url=job_in.application_url,
            source_url=job_in.source_url,
            posted_at=job_in.posted_at,
            is_active=job_in.is_active,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def upsert(self, job_in: JobCreate) -> Tuple[Job, bool]:
        """Upsert a job opening using (career_source_id, external_id) composite key.
        
        If a job with the given career_source_id and external_id already exists:
            - Refreshes last_seen_at timestamp to now (UTC).
            - Updates mutable attributes (title, description, urls, location).
            - Ensures is_active is set to True.
            - Returns (job, False) indicating an update.
        Otherwise:
            - Inserts a new job record.
            - Returns (job, True) indicating a new record was created.
        """
        existing: Optional[Job] = None
        if job_in.external_id:
            existing = self.get_by_external_id(
                job_in.career_source_id,
                job_in.external_id,
            )

        now_utc = datetime.now(timezone.utc)

        if existing is not None:
            # Update attributes and refresh last_seen_at
            existing.title = job_in.title
            if job_in.description is not None:
                existing.description = job_in.description
            if job_in.location is not None:
                existing.location = job_in.location
            if job_in.employment_type is not None:
                existing.employment_type = job_in.employment_type
            if job_in.workplace_type is not None:
                existing.workplace_type = job_in.workplace_type
            if job_in.application_url is not None:
                existing.application_url = job_in.application_url
            if job_in.source_url is not None:
                existing.source_url = job_in.source_url
            if job_in.posted_at is not None:
                existing.posted_at = job_in.posted_at
            existing.is_active = True
            existing.last_seen_at = now_utc

            self.db.commit()
            self.db.refresh(existing)
            return existing, False

        # Create new job
        new_job = Job(
            company_id=job_in.company_id,
            career_source_id=job_in.career_source_id,
            external_id=job_in.external_id,
            title=job_in.title,
            description=job_in.description,
            location=job_in.location,
            employment_type=job_in.employment_type,
            workplace_type=job_in.workplace_type,
            application_url=job_in.application_url,
            source_url=job_in.source_url,
            posted_at=job_in.posted_at,
            first_seen_at=now_utc,
            last_seen_at=now_utc,
            is_active=job_in.is_active,
        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)
        return new_job, True

    def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """Fetch a single Job by ID."""
        return self.db.get(Job, job_id)

    def get_by_external_id(
        self,
        career_source_id: UUID,
        external_id: str,
    ) -> Optional[Job]:
        """Fetch a job by its career source ID and external ATS identifier."""
        stmt = select(Job).where(
            Job.career_source_id == career_source_id,
            Job.external_id == external_id,
        )
        return self.db.scalars(stmt).first()

    def list_jobs(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """List jobs ordered by first_seen_at descending."""
        stmt = (
            select(Job)
            .order_by(Job.first_seen_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_active(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """List active jobs ordered by first_seen_at descending."""
        stmt = (
            select(Job)
            .where(Job.is_active.is_(True))
            .order_by(Job.first_seen_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_by_company(
        self,
        company_id: UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Job]:
        """List jobs for a specific company."""
        stmt = select(Job).where(Job.company_id == company_id)
        if is_active is not None:
            stmt = stmt.where(Job.is_active.is_(is_active))
        stmt = stmt.order_by(Job.first_seen_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
