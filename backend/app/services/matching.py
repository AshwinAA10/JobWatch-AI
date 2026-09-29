"""MatchingService orchestrating feature extraction, engine evaluation, and persistence."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.matching.engine import MatchingEngine
from app.matching.features import extract_candidate_features, extract_job_features
from app.matching.models import MatchResult
from app.models.job_match import JobMatch
from app.models.job_requirements import JobRequirements
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.job import JobRepository
from app.repositories.job_match import JobMatchRepository
from app.repositories.job_requirements import JobRequirementsRepository
from app.schemas.matching import JobMatchResponse, JobRequirementsCreate
from app.services.exceptions import JobNotFoundError, ProfileNotFoundError


class MatchingService:
    """Service coordinating deterministic matching operations between candidate profiles and jobs."""

    def __init__(
        self,
        db: Session,
        engine: Optional[MatchingEngine] = None,
    ) -> None:
        self.db = db
        self.candidate_profile_repo = CandidateProfileRepository(db)
        self.job_repo = JobRepository(db)
        self.job_requirements_repo = JobRequirementsRepository(db)
        self.job_match_repo = JobMatchRepository(db)
        self.engine = engine or MatchingEngine()

    def match_candidate_to_job(
        self,
        user_id: UUID,
        job_id: UUID,
        persist: bool = True,
    ) -> JobMatchResponse:
        """Evaluate how well an authenticated user's candidate profile matches a specific job."""
        profile = self.candidate_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(user_id=user_id)

        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        requirements = self.job_requirements_repo.get_by_job_id(job_id)

        cand_features = extract_candidate_features(profile)
        job_features = extract_job_features(job, requirements)

        match_result: MatchResult = self.engine.match(cand_features, job_features)

        match_id = None
        calc_at = None

        if persist:
            persisted = self.job_match_repo.upsert_match(
                user_id=user_id,
                profile_id=profile.id,
                job_id=job_id,
                score=match_result.score,
                scoring_version=match_result.scoring_version,
                breakdown=match_result.breakdown,
                matched_criteria=match_result.matched_criteria,
                missing_criteria=match_result.missing_criteria,
                mismatches=match_result.mismatches,
                reasons=match_result.reasons,
            )
            match_id = persisted.id
            calc_at = persisted.calculated_at

        return JobMatchResponse(
            id=match_id,
            job_id=job_id,
            profile_id=profile.id,
            score=match_result.score,
            confidence=match_result.confidence,
            scoring_version=match_result.scoring_version,
            breakdown=match_result.breakdown,
            matched_criteria=match_result.matched_criteria,
            missing_criteria=match_result.missing_criteria,
            mismatches=match_result.mismatches,
            reasons=match_result.reasons,
            calculated_at=calc_at,
        )

    def get_match(self, user_id: UUID, job_id: UUID) -> Optional[JobMatch]:
        """Fetch previously calculated match result for the authenticated user and job."""
        profile = self.candidate_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(user_id=user_id)

        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        return self.job_match_repo.get_by_profile_and_job(profile.id, job_id)

    def list_matches_for_user(
        self,
        user_id: UUID,
        min_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[JobMatch]:
        """List previously calculated match results for the authenticated user."""
        profile = self.candidate_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(user_id=user_id)

        return self.job_match_repo.list_for_profile(
            profile_id=profile.id,
            min_score=min_score,
            skip=skip,
            limit=limit,
        )

    def set_job_requirements(
        self,
        job_id: UUID,
        data: JobRequirementsCreate,
    ) -> JobRequirements:
        """Create or update structured requirements for a job opening."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        return self.job_requirements_repo.upsert(
            job_id=job_id,
            required_skills=data.required_skills,
            preferred_skills=data.preferred_skills,
            minimum_experience_years=data.minimum_experience_years,
            maximum_experience_years=data.maximum_experience_years,
            minimum_salary=data.minimum_salary,
            maximum_salary=data.maximum_salary,
            salary_currency=data.salary_currency,
            required_education_level=data.required_education_level,
        )

    def get_job_requirements(self, job_id: UUID) -> Optional[JobRequirements]:
        """Fetch structured requirements for a job opening."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        return self.job_requirements_repo.get_by_job_id(job_id)
