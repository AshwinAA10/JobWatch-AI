"""Repository for CandidateProfile data access operations."""

from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_preferences import CandidatePreferences
from app.models.education import Education
from app.models.experience import Experience
from app.schemas.candidate_profile import CandidateProfileCreate


class CandidateProfileRepository:
    """Data access repository for CandidateProfile entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self, user_id: UUID, profile_in: CandidateProfileCreate
    ) -> CandidateProfile:
        """Create and persist a new candidate profile for a user."""
        profile = CandidateProfile(
            user_id=user_id,
            first_name=profile_in.first_name,
            last_name=profile_in.last_name,
            headline=profile_in.headline,
            bio=profile_in.bio,
            phone=profile_in.phone,
            city=profile_in.city,
            state=profile_in.state,
            country=profile_in.country,
            years_of_experience=profile_in.years_of_experience,
            current_job_title=profile_in.current_job_title,
            current_company=profile_in.current_company,
            highest_education_level=profile_in.highest_education_level,
            profile_visibility=profile_in.profile_visibility.value,
            profile_completion_percent=0,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_by_id(self, profile_id: UUID) -> Optional[CandidateProfile]:
        """Fetch a profile by UUID primary key."""
        return self.db.get(CandidateProfile, profile_id)

    def get_by_user_id(
        self, user_id: UUID, load_relations: bool = False
    ) -> Optional[CandidateProfile]:
        """Fetch a candidate profile by its owning user UUID.

        When load_relations is True, efficiently preloads child entities (skills,
        experiences, educations, preferences) to avoid N+1 query patterns.
        """
        stmt = select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.educations),
                selectinload(CandidateProfile.preferences),
            )
        return self.db.scalars(stmt).first()

    def update(
        self, profile: CandidateProfile, update_data: Dict[str, Any]
    ) -> CandidateProfile:
        """Update explicit fields on a profile entity."""
        for field, value in update_data.items():
            if hasattr(profile, field):
                if hasattr(value, "value"):
                    value = value.value
                setattr(profile, field, value)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_completion_percent(
        self, profile_id: UUID, percent: int
    ) -> None:
        """Update the profile completion score."""
        stmt = (
            update(CandidateProfile)
            .where(CandidateProfile.id == profile_id)
            .values(profile_completion_percent=percent)
        )
        self.db.execute(stmt)
        self.db.commit()
