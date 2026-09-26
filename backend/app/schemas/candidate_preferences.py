"""Pydantic schemas for CandidatePreferences entity."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.enums import EmploymentType, WorkplaceType


class CandidatePreferencesUpdate(BaseModel):
    """Payload to create or update candidate preferences."""

    desired_titles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    workplace_types: Optional[List[WorkplaceType]] = None
    employment_types: Optional[List[EmploymentType]] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: Optional[str] = "USD"
    minimum_experience_years: Optional[int] = None
    maximum_experience_years: Optional[int] = None
    willing_to_relocate: Optional[bool] = False
    remote_preference: Optional[str] = None

    @field_validator("salary_currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> str:
        if v:
            v = v.strip().upper()
            if len(v) != 3:
                raise ValueError("Currency must be a 3-letter ISO code (e.g., USD, EUR, INR)")
            return v
        return "USD"

    @model_validator(mode="after")
    def validate_ranges(self) -> "CandidatePreferencesUpdate":
        if self.minimum_salary is not None and self.minimum_salary < 0:
            raise ValueError("Minimum salary cannot be negative")
        if self.maximum_salary is not None and self.maximum_salary < 0:
            raise ValueError("Maximum salary cannot be negative")
        if (
            self.minimum_salary is not None
            and self.maximum_salary is not None
            and self.maximum_salary < self.minimum_salary
        ):
            raise ValueError("Maximum salary cannot be less than minimum salary")

        if self.minimum_experience_years is not None and self.minimum_experience_years < 0:
            raise ValueError("Minimum experience years cannot be negative")
        if self.maximum_experience_years is not None and self.maximum_experience_years < 0:
            raise ValueError("Maximum experience years cannot be negative")
        if (
            self.minimum_experience_years is not None
            and self.maximum_experience_years is not None
            and self.maximum_experience_years < self.minimum_experience_years
        ):
            raise ValueError("Maximum experience years cannot be less than minimum experience years")
        return self


class CandidatePreferencesResponse(BaseModel):
    """Response schema for CandidatePreferences."""

    id: UUID
    profile_id: UUID
    desired_titles: List[str]
    preferred_locations: List[str]
    workplace_types: List[str]
    employment_types: List[str]
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: str
    minimum_experience_years: Optional[int] = None
    maximum_experience_years: Optional[int] = None
    willing_to_relocate: bool
    remote_preference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
