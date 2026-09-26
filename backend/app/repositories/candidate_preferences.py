"""Repository for CandidatePreferences data access operations."""

from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_preferences import CandidatePreferences
from app.schemas.candidate_preferences import CandidatePreferencesUpdate


class CandidatePreferencesRepository:
    """Data access repository for CandidatePreferences entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_profile_id(self, profile_id: UUID) -> Optional[CandidatePreferences]:
        """Fetch preferences for a candidate profile."""
        stmt = select(CandidatePreferences).where(
            CandidatePreferences.profile_id == profile_id
        )
        return self.db.scalars(stmt).first()

    def create_or_update(
        self, profile_id: UUID, prefs_in: CandidatePreferencesUpdate
    ) -> CandidatePreferences:
        """Create or update preferences for a profile."""
        prefs = self.get_by_profile_id(profile_id)
        if not prefs:
            prefs = CandidatePreferences(
                profile_id=profile_id,
                desired_titles=prefs_in.desired_titles or [],
                preferred_locations=prefs_in.preferred_locations or [],
                workplace_types=[
                    w.value if hasattr(w, "value") else str(w)
                    for w in (prefs_in.workplace_types or [])
                ],
                employment_types=[
                    e.value if hasattr(e, "value") else str(e)
                    for e in (prefs_in.employment_types or [])
                ],
                minimum_salary=prefs_in.minimum_salary,
                maximum_salary=prefs_in.maximum_salary,
                salary_currency=prefs_in.salary_currency or "USD",
                minimum_experience_years=prefs_in.minimum_experience_years,
                maximum_experience_years=prefs_in.maximum_experience_years,
                willing_to_relocate=prefs_in.willing_to_relocate or False,
                remote_preference=prefs_in.remote_preference,
            )
            self.db.add(prefs)
        else:
            if prefs_in.desired_titles is not None:
                prefs.desired_titles = prefs_in.desired_titles
            if prefs_in.preferred_locations is not None:
                prefs.preferred_locations = prefs_in.preferred_locations
            if prefs_in.workplace_types is not None:
                prefs.workplace_types = [
                    w.value if hasattr(w, "value") else str(w)
                    for w in prefs_in.workplace_types
                ]
            if prefs_in.employment_types is not None:
                prefs.employment_types = [
                    e.value if hasattr(e, "value") else str(e)
                    for e in prefs_in.employment_types
                ]
            if prefs_in.minimum_salary is not None:
                prefs.minimum_salary = prefs_in.minimum_salary
            if prefs_in.maximum_salary is not None:
                prefs.maximum_salary = prefs_in.maximum_salary
            if prefs_in.salary_currency is not None:
                prefs.salary_currency = prefs_in.salary_currency
            if prefs_in.minimum_experience_years is not None:
                prefs.minimum_experience_years = prefs_in.minimum_experience_years
            if prefs_in.maximum_experience_years is not None:
                prefs.maximum_experience_years = prefs_in.maximum_experience_years
            if prefs_in.willing_to_relocate is not None:
                prefs.willing_to_relocate = prefs_in.willing_to_relocate
            if prefs_in.remote_preference is not None:
                prefs.remote_preference = prefs_in.remote_preference
            self.db.add(prefs)

        self.db.commit()
        self.db.refresh(prefs)
        return prefs
