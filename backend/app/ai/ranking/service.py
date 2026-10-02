"""Personalized job ranking and recommendation service integrating feedback signals."""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.repositories.application import ApplicationRepository
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.job import JobRepository
from app.repositories.saved_job import SavedJobRepository


class PersonalizedRankingService:
    """Adjusts job recommendations and rankings according to candidate history and interaction signals."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        if db is not None:
            self.job_repo = JobRepository(db)
            self.profile_repo = CandidateProfileRepository(db)
            self.saved_repo = SavedJobRepository(db)
            self.app_repo = ApplicationRepository(db)

    def compute_personalized_boost(
        self,
        job: Job,
        profile: CandidateProfile,
        saved_job_ids: Set[UUID],
        applied_job_ids: Set[UUID],
    ) -> float:
        """Compute an interaction-aware adjustment to ranking score (-20.0 to +15.0).
        
        Signals:
        - Already applied: negative boost (-20.0) so already processed jobs don't clutter top suggestions.
        - Bookmarked/Saved: positive engagement signal (+8.0).
        - Matching preferred title keyword: (+5.0).
        - Matching preferred location: (+5.0).
        - Matching preferred workplace type: (+5.0).
        """
        boost = 0.0

        if job.id in applied_job_ids:
            boost -= 20.0
        elif job.id in saved_job_ids:
            boost += 8.0

        # Candidate preferences alignment
        pref = profile.preferences
        if pref:
            if pref.preferred_workplace_type and job.workplace_type == pref.preferred_workplace_type.value:
                boost += 5.0
            if pref.preferred_locations and job.location:
                for loc in pref.preferred_locations:
                    if loc.lower() in job.location.lower():
                        boost += 5.0
                        break
            if pref.preferred_titles:
                for title in pref.preferred_titles:
                    if title.lower() in job.title.lower():
                        boost += 5.0
                        break

        return boost

    def rank_jobs_for_candidate(
        self,
        profile_id: UUID,
        jobs: List[Job],
        base_scores: Optional[Dict[UUID, float]] = None,
    ) -> List[Dict[str, Any]]:
        """Rank a collection of jobs applying candidate interaction signals."""
        profile = self.profile_repo.get_by_id(profile_id)
        if not profile:
            return [{"job": j, "final_rank_score": 50.0} for j in jobs]

        saved_ids = self.saved_repo.get_saved_job_ids(profile_id)
        user_apps, _ = self.app_repo.list_for_profile(profile_id, limit=500)
        applied_ids = {a.job_id for a in user_apps if a.job_id}

        ranked = []
        for job in jobs:
            base_score = (base_scores or {}).get(job.id, 50.0)
            boost = self.compute_personalized_boost(job, profile, saved_ids, applied_ids)
            final_score = round(max(0.0, min(100.0, base_score + boost)), 1)
            ranked.append({
                "job": job,
                "base_score": base_score,
                "personalization_boost": boost,
                "final_rank_score": final_score,
            })

        ranked.sort(key=lambda x: x["final_rank_score"], reverse=True)
        return ranked
