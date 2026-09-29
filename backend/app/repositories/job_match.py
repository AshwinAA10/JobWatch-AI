"""Repository for JobMatch persistence operations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_match import JobMatch


class JobMatchRepository:
    """Data access repository for JobMatch entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_profile_and_job(self, profile_id: UUID, job_id: UUID) -> Optional[JobMatch]:
        """Fetch match result for a specific candidate profile and job pair."""
        stmt = (
            select(JobMatch)
            .where(
                JobMatch.profile_id == profile_id,
                JobMatch.job_id == job_id,
            )
        )
        return self.db.scalars(stmt).first()

    def upsert_match(
        self,
        user_id: UUID,
        profile_id: UUID,
        job_id: UUID,
        score: float,
        scoring_version: str,
        breakdown: Dict[str, Any],
        matched_criteria: List[str],
        missing_criteria: List[str],
        mismatches: List[str],
        reasons: List[str],
    ) -> JobMatch:
        """Create or update a JobMatch record for a profile and job pair."""
        existing = self.get_by_profile_and_job(profile_id, job_id)
        if existing:
            existing.user_id = user_id
            existing.score = score
            existing.scoring_version = scoring_version
            existing.breakdown = breakdown
            existing.matched_criteria = matched_criteria
            existing.missing_criteria = missing_criteria
            existing.mismatches = mismatches
            existing.reasons = reasons
            existing.calculated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        match_record = JobMatch(
            user_id=user_id,
            profile_id=profile_id,
            job_id=job_id,
            score=score,
            scoring_version=scoring_version,
            breakdown=breakdown,
            matched_criteria=matched_criteria,
            missing_criteria=missing_criteria,
            mismatches=mismatches,
            reasons=reasons,
            calculated_at=datetime.now(timezone.utc),
        )
        self.db.add(match_record)
        self.db.commit()
        self.db.refresh(match_record)
        return match_record

    def list_for_profile(
        self,
        profile_id: UUID,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[JobMatch]:
        """Retrieve matches for a candidate profile ordered by score descending."""
        stmt = select(JobMatch).where(JobMatch.profile_id == profile_id)
        if min_score is not None:
            stmt = stmt.where(JobMatch.score >= min_score)
        stmt = stmt.order_by(JobMatch.score.desc(), JobMatch.calculated_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_for_job(
        self,
        job_id: UUID,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[JobMatch]:
        """Retrieve matches for a specific job ordered by score descending."""
        stmt = select(JobMatch).where(JobMatch.job_id == job_id)
        if min_score is not None:
            stmt = stmt.where(JobMatch.score >= min_score)
        stmt = stmt.order_by(JobMatch.score.desc(), JobMatch.calculated_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
