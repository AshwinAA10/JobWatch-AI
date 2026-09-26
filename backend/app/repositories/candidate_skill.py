"""Repository for CandidateSkill data access operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.candidate_skill import CandidateSkill


class CandidateSkillRepository:
    """Data access repository for CandidateSkill association entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        profile_id: UUID,
        skill_id: UUID,
        proficiency: str,
        years_experience: Optional[float] = None,
    ) -> CandidateSkill:
        """Associate a skill with a candidate profile."""
        candidate_skill = CandidateSkill(
            profile_id=profile_id,
            skill_id=skill_id,
            proficiency=proficiency,
            years_experience=years_experience,
        )
        self.db.add(candidate_skill)
        self.db.commit()
        self.db.refresh(candidate_skill)
        return candidate_skill

    def get_by_id(self, skill_assoc_id: UUID) -> Optional[CandidateSkill]:
        """Fetch a candidate skill association by its primary key."""
        stmt = (
            select(CandidateSkill)
            .where(CandidateSkill.id == skill_assoc_id)
            .options(joinedload(CandidateSkill.skill))
        )
        return self.db.scalars(stmt).first()

    def get_by_profile_and_skill(
        self, profile_id: UUID, skill_id: UUID
    ) -> Optional[CandidateSkill]:
        """Fetch association by candidate profile ID and skill ID."""
        stmt = (
            select(CandidateSkill)
            .where(
                CandidateSkill.profile_id == profile_id,
                CandidateSkill.skill_id == skill_id,
            )
            .options(joinedload(CandidateSkill.skill))
        )
        return self.db.scalars(stmt).first()

    def list_for_profile(self, profile_id: UUID) -> List[CandidateSkill]:
        """List all skills attached to a candidate profile."""
        stmt = (
            select(CandidateSkill)
            .where(CandidateSkill.profile_id == profile_id)
            .options(joinedload(CandidateSkill.skill))
            .order_by(CandidateSkill.created_at)
        )
        return list(self.db.scalars(stmt).all())

    def update(
        self,
        candidate_skill: CandidateSkill,
        update_data: Dict[str, Any],
    ) -> CandidateSkill:
        """Update proficiency or years of experience for a candidate skill."""
        for field, value in update_data.items():
            if hasattr(candidate_skill, field):
                setattr(candidate_skill, field, value)
        self.db.add(candidate_skill)
        self.db.commit()
        self.db.refresh(candidate_skill)
        return candidate_skill

    def delete(self, candidate_skill: CandidateSkill) -> None:
        """Remove a skill from a candidate profile."""
        self.db.delete(candidate_skill)
        self.db.commit()
