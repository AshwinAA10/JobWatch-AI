"""DeduplicationService: candidate blocking, evaluation, canonical resolution, and persistence."""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.deduplication.exceptions import (
    CanonicalCycleError,
    JobNotFoundError,
    SelfDuplicateError,
)
from app.deduplication.schemas import MatchResult
from app.deduplication.scoring import evaluate_job_pair
from app.models.job import Job
from app.models.job_duplicate import JobDuplicate
from app.repositories.job_duplicate import JobDuplicateRepository

logger = logging.getLogger("jobwatch.deduplication.service")


class DeduplicationService:
    """Orchestrates candidate retrieval, pairwise similarity evaluation, and duplicate linking."""

    def __init__(
        self,
        db: Session,
        settings: Optional[Settings] = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.dup_repo = JobDuplicateRepository(db)

    def get_candidates(self, job: Job) -> List[Job]:
        """Retrieve candidate matching jobs using index-backed deterministic blocking.
        
        Applies:
            - Same company boundary (Company ID)
            - Excludes target job itself
            - Lookback window filter
            - Configurable candidate limit (avoiding O(N^2) global scan)
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.settings.DEDUP_LOOKBACK_DAYS)

        stmt = (
            select(Job)
            .where(Job.company_id == job.company_id)
            .where(Job.id != job.id)
            .where(Job.first_seen_at >= cutoff_date)
            .order_by(Job.first_seen_at.asc())
            .limit(self.settings.DEDUP_MAX_CANDIDATES)
        )
        return list(self.db.scalars(stmt).all())

    def select_canonical(self, job_a: Job, job_b: Job) -> Tuple[Job, Job]:
        """Deterministically determine which job should be canonical.
        
        Returns:
            Tuple of (canonical_job, duplicate_job)
        """
        # 1. If one job is already established as a canonical root (no canonical_job_id), prefer it
        if job_a.canonical_job_id is None and job_b.canonical_job_id is not None:
            return job_a, job_b
        if str(job_b.canonical_job_id) == str(job_a.id):
            return job_a, job_b
        if job_b.canonical_job_id is None and job_a.canonical_job_id is not None:
            return job_b, job_a
        if str(job_a.canonical_job_id) == str(job_b.id):
            return job_b, job_a

        # 2. Prefer earliest discovery timestamp (first_seen_at)
        time_a = job_a.first_seen_at or job_a.created_at
        time_b = job_b.first_seen_at or job_b.created_at
        if time_a and time_b and time_a != time_b:
            if time_a < time_b:
                return job_a, job_b
            return job_b, job_a

        # 3. Prefer more complete metadata
        score_a = sum(1 for v in [job_a.description, job_a.application_url, job_a.location, job_a.workplace_type] if v)
        score_b = sum(1 for v in [job_b.description, job_b.application_url, job_b.location, job_b.workplace_type] if v)
        if score_a != score_b:
            if score_a > score_b:
                return job_a, job_b
            return job_b, job_a

        # 4. Tie-breaker: stable UUID string order
        if str(job_a.id) < str(job_b.id):
            return job_a, job_b
        return job_b, job_a

    def resolve_canonical_root(self, job: Job) -> Job:
        """Resolve the root canonical job, preventing canonical chaining (A -> B -> C)."""
        current = job
        visited = {str(current.id)}
        depth = 0

        while current.canonical_job_id is not None and depth < 10:
            depth += 1
            parent_id = current.canonical_job_id
            if str(parent_id) in visited:
                raise CanonicalCycleError(f"Canonical cycle detected at job {parent_id}")
            visited.add(str(parent_id))
            parent = self.db.get(Job, parent_id)
            if parent is None:
                # Orphaned canonical pointer - clear it
                current.canonical_job_id = None
                self.db.commit()
                break
            current = parent

        return current

    def evaluate_pair(self, job_a: Job, job_b: Job) -> MatchResult:
        """Evaluate match confidence between two jobs."""
        return evaluate_job_pair(
            job_a=job_a,
            job_b=job_b,
            high_threshold=self.settings.DEDUP_HIGH_THRESHOLD,
            medium_threshold=self.settings.DEDUP_MEDIUM_THRESHOLD,
        )

    def deduplicate_job(self, job_id: UUID) -> Optional[JobDuplicate]:
        """Execute deduplication for an individual job, creating a duplicate link if a match meets the threshold."""
        if not self.settings.DEDUP_ENABLED:
            return None

        target_job = self.db.get(Job, job_id)
        if not target_job:
            raise JobNotFoundError(f"Job with ID '{job_id}' not found", job_id=job_id)

        candidates = self.get_candidates(target_job)
        if not candidates:
            return None

        for candidate in candidates:
            result = self.evaluate_pair(target_job, candidate)

            if result.score >= self.settings.DEDUP_HIGH_THRESHOLD:
                # High confidence match: establish duplicate relationship
                canonical_candidate, duplicate_candidate = self.select_canonical(target_job, candidate)
                root_canonical = self.resolve_canonical_root(canonical_candidate)

                if root_canonical.id == duplicate_candidate.id:
                    continue  # Self duplicate safety guard

                # Check if relationship already exists
                existing_record = self.dup_repo.get_by_duplicate_id(duplicate_candidate.id)
                if existing_record:
                    return existing_record

                # Link duplicate to canonical root
                duplicate_candidate.canonical_job_id = root_canonical.id
                self.db.add(duplicate_candidate)
                self.db.commit()

                duplicate_record = self.dup_repo.create(
                    canonical_job_id=root_canonical.id,
                    duplicate_job_id=duplicate_candidate.id,
                    match_type=result.match_type,
                    confidence_score=result.score,
                    matched_fields=result.matched_fields,
                    reason=result.reason,
                )

                logger.info(
                    "Linked duplicate job %s -> canonical %s (score: %.2f, type: %s)",
                    duplicate_candidate.id,
                    root_canonical.id,
                    result.score,
                    result.match_type,
                )
                return duplicate_record

        return None

    def deduplicate_batch(self, jobs: List[Job]) -> List[JobDuplicate]:
        """Run deduplication across a collection of newly ingested or updated jobs."""
        if not self.settings.DEDUP_ENABLED:
            return []

        created_duplicates: List[JobDuplicate] = []
        for job in jobs:
            try:
                dup = self.deduplicate_job(job.id)
                if dup:
                    created_duplicates.append(dup)
            except Exception as exc:
                logger.exception("Error running deduplication for job %s: %s", job.id, exc)

        return created_duplicates
