"""Repository for Experience data access operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.experience import Experience
from app.schemas.experience import ExperienceCreate


class ExperienceRepository:
    """Data access repository for candidate Experience entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, profile_id: UUID, exp_in: ExperienceCreate) -> Experience:
        """Create a new work experience record for a profile."""
        exp = Experience(
            profile_id=profile_id,
            company_name=exp_in.company_name,
            job_title=exp_in.job_title,
            description=exp_in.description,
            location=exp_in.location,
            employment_type=exp_in.employment_type,
            start_date=exp_in.start_date,
            end_date=exp_in.end_date,
            is_current=exp_in.is_current,
        )
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)
        return exp

    def get_by_id(self, exp_id: UUID) -> Optional[Experience]:
        """Fetch an experience record by UUID."""
        return self.db.get(Experience, exp_id)

    def list_for_profile(self, profile_id: UUID) -> List[Experience]:
        """List experiences for a profile sorted chronologically descending."""
        stmt = (
            select(Experience)
            .where(Experience.profile_id == profile_id)
            .order_by(desc(Experience.start_date))
        )
        return list(self.db.scalars(stmt).all())

    def update(self, exp: Experience, update_data: Dict[str, Any]) -> Experience:
        """Update explicit fields on an experience record."""
        for field, value in update_data.items():
            if hasattr(exp, field):
                setattr(exp, field, value)
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)
        return exp

    def delete(self, exp: Experience) -> None:
        """Delete an experience record."""
        self.db.delete(exp)
        self.db.commit()
