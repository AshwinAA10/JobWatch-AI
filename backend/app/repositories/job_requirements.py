"""Repository for JobRequirements persistence operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_requirements import JobRequirements


class JobRequirementsRepository:
    """Data access repository for JobRequirements entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(self, job_id: UUID) -> Optional[JobRequirements]:
        """Fetch JobRequirements for a specific job."""
        stmt = select(JobRequirements).where(JobRequirements.job_id == job_id)
        return self.db.scalars(stmt).first()

    def upsert(
        self,
        job_id: UUID,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        minimum_experience_years: Optional[float] = None,
        maximum_experience_years: Optional[float] = None,
        minimum_salary: Optional[int] = None,
        maximum_salary: Optional[int] = None,
        salary_currency: Optional[str] = "USD",
        required_education_level: Optional[str] = None,
    ) -> JobRequirements:
        """Create or update JobRequirements for a job."""
        existing = self.get_by_job_id(job_id)
        if existing:
            if required_skills is not None:
                existing.required_skills = required_skills
            if preferred_skills is not None:
                existing.preferred_skills = preferred_skills
            if minimum_experience_years is not None:
                existing.minimum_experience_years = minimum_experience_years
            if maximum_experience_years is not None:
                existing.maximum_experience_years = maximum_experience_years
            if minimum_salary is not None:
                existing.minimum_salary = minimum_salary
            if maximum_salary is not None:
                existing.maximum_salary = maximum_salary
            if salary_currency is not None:
                existing.salary_currency = salary_currency
            if required_education_level is not None:
                existing.required_education_level = required_education_level
            self.db.commit()
            self.db.refresh(existing)
            return existing

        requirements = JobRequirements(
            job_id=job_id,
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
            minimum_experience_years=minimum_experience_years,
            maximum_experience_years=maximum_experience_years,
            minimum_salary=minimum_salary,
            maximum_salary=maximum_salary,
            salary_currency=salary_currency,
            required_education_level=required_education_level,
        )
        self.db.add(requirements)
        self.db.commit()
        self.db.refresh(requirements)
        return requirements

    def delete(self, job_id: UUID) -> bool:
        """Delete JobRequirements for a job."""
        existing = self.get_by_job_id(job_id)
        if existing:
            self.db.delete(existing)
            self.db.commit()
            return True
        return False
