"""Service orchestrating candidate profiles, skills, experience, education, and preferences."""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.education import Education
from app.models.experience import Experience
from app.repositories.candidate_preferences import CandidatePreferencesRepository
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.candidate_skill import CandidateSkillRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.skill import SkillRepository
from app.schemas.candidate_preferences import CandidatePreferencesUpdate
from app.schemas.candidate_profile import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
    ProfileCompletenessResponse,
)
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.schemas.skill import CandidateSkillCreate, CandidateSkillUpdate
from app.services.exceptions import (
    DuplicateSkillError,
    ProfileNotFoundError,
    ResourceNotFoundError,
    UnauthorizedAccessError,
)
from app.services.profile_completeness import ProfileCompletenessService


class ProfileService:
    """Orchestrates candidate profile domain operations and maintains completeness metrics."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.profile_repo = CandidateProfileRepository(db)
        self.skill_repo = SkillRepository(db)
        self.candidate_skill_repo = CandidateSkillRepository(db)
        self.exp_repo = ExperienceRepository(db)
        self.edu_repo = EducationRepository(db)
        self.prefs_repo = CandidatePreferencesRepository(db)

    def _refresh_completeness(self, profile: CandidateProfile) -> None:
        """Recalculate and persist the profile completeness percentage."""
        self.db.expire_all()
        full_profile = self.profile_repo.get_by_user_id(profile.user_id, load_relations=True)
        if full_profile:
            score, _, _ = ProfileCompletenessService.calculate(full_profile)
            self.profile_repo.update_completion_percent(full_profile.id, score)

    def get_or_create_profile(
        self, user_id: UUID, profile_in: Optional[CandidateProfileCreate] = None
    ) -> CandidateProfile:
        """Fetch candidate profile for a user, creating it if it doesn't already exist."""
        profile = self.profile_repo.get_by_user_id(user_id, load_relations=True)
        if not profile:
            profile_create = profile_in or CandidateProfileCreate()
            profile = self.profile_repo.create(user_id, profile_create)
            self._refresh_completeness(profile)
            profile = self.profile_repo.get_by_user_id(user_id, load_relations=True)
        return profile

    def get_profile(self, user_id: UUID) -> CandidateProfile:
        """Fetch full candidate profile with child collections, or raise ProfileNotFoundError."""
        profile = self.profile_repo.get_by_user_id(user_id, load_relations=True)
        if not profile:
            raise ProfileNotFoundError(user_id)
        return profile

    def update_profile(
        self, user_id: UUID, profile_in: CandidateProfileUpdate
    ) -> CandidateProfile:
        """Update candidate profile attributes."""
        profile = self.get_or_create_profile(user_id)
        update_data = profile_in.model_dump(exclude_unset=True)
        profile = self.profile_repo.update(profile, update_data)
        self._refresh_completeness(profile)
        return self.get_profile(user_id)

    # --- Skills Management ---

    def add_skill(
        self, user_id: UUID, skill_in: CandidateSkillCreate
    ) -> CandidateSkill:
        """Attach a skill to candidate profile."""
        profile = self.get_or_create_profile(user_id)

        # Resolve skill entity
        if skill_in.skill_id:
            skill = self.skill_repo.get_by_id(skill_in.skill_id)
            if not skill:
                raise ResourceNotFoundError(f"Skill with ID {skill_in.skill_id} not found")
        elif skill_in.skill_name:
            skill = self.skill_repo.get_or_create(skill_in.skill_name)
        else:
            raise ValueError("Either skill_id or skill_name must be provided")

        # Check for existing association
        existing = self.candidate_skill_repo.get_by_profile_and_skill(
            profile.id, skill.id
        )
        if existing:
            raise DuplicateSkillError(f"Skill '{skill.name}' is already attached to this profile")

        candidate_skill = self.candidate_skill_repo.create(
            profile_id=profile.id,
            skill_id=skill.id,
            proficiency=skill_in.proficiency.value,
            years_experience=skill_in.years_experience,
        )
        self._refresh_completeness(profile)
        return self.candidate_skill_repo.get_by_id(candidate_skill.id)

    def update_skill(
        self, user_id: UUID, skill_assoc_id: UUID, update_in: CandidateSkillUpdate
    ) -> CandidateSkill:
        """Update proficiency or experience on an attached skill."""
        profile = self.get_or_create_profile(user_id)
        assoc = self.candidate_skill_repo.get_by_id(skill_assoc_id)
        if not assoc:
            raise ResourceNotFoundError(f"Skill association {skill_assoc_id} not found")
        if assoc.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot modify skill belonging to another profile")

        update_data = {}
        if update_in.proficiency is not None:
            update_data["proficiency"] = update_in.proficiency.value
        if update_in.years_experience is not None:
            update_data["years_experience"] = update_in.years_experience

        updated = self.candidate_skill_repo.update(assoc, update_data)
        self._refresh_completeness(profile)
        return updated

    def remove_skill(self, user_id: UUID, skill_assoc_id: UUID) -> None:
        """Remove a skill from the candidate profile."""
        profile = self.get_or_create_profile(user_id)
        assoc = self.candidate_skill_repo.get_by_id(skill_assoc_id)
        if not assoc:
            raise ResourceNotFoundError(f"Skill association {skill_assoc_id} not found")
        if assoc.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot delete skill belonging to another profile")

        self.candidate_skill_repo.delete(assoc)
        self._refresh_completeness(profile)

    # --- Work Experience Management ---

    def add_experience(
        self, user_id: UUID, exp_in: ExperienceCreate
    ) -> Experience:
        """Add a work experience entry to the candidate profile."""
        profile = self.get_or_create_profile(user_id)
        exp = self.exp_repo.create(profile.id, exp_in)
        self._refresh_completeness(profile)
        return exp

    def update_experience(
        self, user_id: UUID, exp_id: UUID, exp_in: ExperienceUpdate
    ) -> Experience:
        """Update an existing work experience record."""
        profile = self.get_or_create_profile(user_id)
        exp = self.exp_repo.get_by_id(exp_id)
        if not exp:
            raise ResourceNotFoundError(f"Experience entry {exp_id} not found")
        if exp.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot modify experience belonging to another profile")

        update_data = exp_in.model_dump(exclude_unset=True)
        updated = self.exp_repo.update(exp, update_data)
        self._refresh_completeness(profile)
        return updated

    def remove_experience(self, user_id: UUID, exp_id: UUID) -> None:
        """Delete an experience record from the profile."""
        profile = self.get_or_create_profile(user_id)
        exp = self.exp_repo.get_by_id(exp_id)
        if not exp:
            raise ResourceNotFoundError(f"Experience entry {exp_id} not found")
        if exp.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot delete experience belonging to another profile")

        self.exp_repo.delete(exp)
        self._refresh_completeness(profile)

    # --- Education History Management ---

    def add_education(
        self, user_id: UUID, edu_in: EducationCreate
    ) -> Education:
        """Add an academic history record to the profile."""
        profile = self.get_or_create_profile(user_id)
        edu = self.edu_repo.create(profile.id, edu_in)
        self._refresh_completeness(profile)
        return edu

    def update_education(
        self, user_id: UUID, edu_id: UUID, edu_in: EducationUpdate
    ) -> Education:
        """Update an existing education record."""
        profile = self.get_or_create_profile(user_id)
        edu = self.edu_repo.get_by_id(edu_id)
        if not edu:
            raise ResourceNotFoundError(f"Education entry {edu_id} not found")
        if edu.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot modify education belonging to another profile")

        update_data = edu_in.model_dump(exclude_unset=True)
        updated = self.edu_repo.update(edu, update_data)
        self._refresh_completeness(profile)
        return updated

    def remove_education(self, user_id: UUID, edu_id: UUID) -> None:
        """Delete an education record from the profile."""
        profile = self.get_or_create_profile(user_id)
        edu = self.edu_repo.get_by_id(edu_id)
        if not edu:
            raise ResourceNotFoundError(f"Education entry {edu_id} not found")
        if edu.profile_id != profile.id:
            raise UnauthorizedAccessError("Cannot delete education belonging to another profile")

        self.edu_repo.delete(edu)
        self._refresh_completeness(profile)

    # --- Preferences Management ---

    def update_preferences(
        self, user_id: UUID, prefs_in: CandidatePreferencesUpdate
    ) -> CandidatePreferences:
        """Create or update structured job search preferences."""
        profile = self.get_or_create_profile(user_id)
        prefs = self.prefs_repo.create_or_update(profile.id, prefs_in)
        self._refresh_completeness(profile)
        return prefs

    def get_preferences(self, user_id: UUID) -> CandidatePreferences:
        """Fetch job search preferences for the user's profile."""
        profile = self.get_or_create_profile(user_id)
        prefs = self.prefs_repo.get_by_profile_id(profile.id)
        if not prefs:
            prefs = self.prefs_repo.create_or_update(
                profile.id, CandidatePreferencesUpdate()
            )
        return prefs

    # --- Completeness Metric ---

    def get_completeness(self, user_id: UUID) -> ProfileCompletenessResponse:
        """Calculate and return profile completeness breakdown."""
        profile = self.get_or_create_profile(user_id)
        return ProfileCompletenessService.get_completeness_response(profile)
