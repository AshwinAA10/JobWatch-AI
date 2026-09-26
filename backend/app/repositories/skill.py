"""Repository for Skill data access operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill


class SkillRepository:
    """Data access repository for canonical Skill entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def normalize_name(name: str) -> str:
        """Deterministically normalize a skill name for uniqueness and indexing."""
        return name.strip().lower()

    def get_by_id(self, skill_id: UUID) -> Optional[Skill]:
        """Fetch a skill by UUID."""
        return self.db.get(Skill, skill_id)

    def get_by_normalized_name(self, normalized_name: str) -> Optional[Skill]:
        """Fetch a skill by its unique normalized name."""
        stmt = select(Skill).where(Skill.normalized_name == normalized_name)
        return self.db.scalars(stmt).first()

    def get_or_create(self, name: str, category: Optional[str] = None) -> Skill:
        """Fetch an existing skill or create a new canonical skill record."""
        clean_name = name.strip()
        normalized = self.normalize_name(clean_name)
        existing = self.get_by_normalized_name(normalized)
        if existing:
            return existing

        skill = Skill(
            name=clean_name,
            normalized_name=normalized,
            category=category.strip() if category else None,
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def search(self, query: str, limit: int = 20) -> List[Skill]:
        """Search skills by name prefix or substring."""
        pattern = f"%{query.strip().lower()}%"
        stmt = (
            select(Skill)
            .where(Skill.normalized_name.like(pattern))
            .order_by(Skill.name)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
