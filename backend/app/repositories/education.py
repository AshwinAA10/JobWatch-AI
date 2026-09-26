"""Repository for Education data access operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.education import Education
from app.schemas.education import EducationCreate


class EducationRepository:
    """Data access repository for candidate Education entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, profile_id: UUID, edu_in: EducationCreate) -> Education:
        """Create a new education record for a profile."""
        edu = Education(
            profile_id=profile_id,
            institution_name=edu_in.institution_name,
            degree=edu_in.degree,
            field_of_study=edu_in.field_of_study,
            location=edu_in.location,
            start_date=edu_in.start_date,
            end_date=edu_in.end_date,
            grade=edu_in.grade,
            description=edu_in.description,
        )
        self.db.add(edu)
        self.db.commit()
        self.db.refresh(edu)
        return edu

    def get_by_id(self, edu_id: UUID) -> Optional[Education]:
        """Fetch an education record by UUID."""
        return self.db.get(Education, edu_id)

    def list_for_profile(self, profile_id: UUID) -> List[Education]:
        """List educations for a profile sorted chronologically descending."""
        stmt = (
            select(Education)
            .where(Education.profile_id == profile_id)
            .order_by(desc(Education.start_date))
        )
        return list(self.db.scalars(stmt).all())

    def update(self, edu: Education, update_data: Dict[str, Any]) -> Education:
        """Update explicit fields on an education record."""
        for field, value in update_data.items():
            if hasattr(edu, field):
                setattr(edu, field, value)
        self.db.add(edu)
        self.db.commit()
        self.db.refresh(edu)
        return edu

    def delete(self, edu: Education) -> None:
        """Delete an education record."""
        self.db.delete(edu)
        self.db.commit()
