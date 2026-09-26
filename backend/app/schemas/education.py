"""Pydantic schemas for Education entity."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator


class EducationCreate(BaseModel):
    """Payload to add an academic history record."""

    institution_name: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "EducationCreate":
        self.institution_name = self.institution_name.strip()
        if not self.institution_name:
            raise ValueError("Institution name cannot be empty")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date")
        return self


class EducationUpdate(BaseModel):
    """Payload to update an existing academic history record."""

    institution_name: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "EducationUpdate":
        if self.institution_name is not None:
            self.institution_name = self.institution_name.strip()
            if not self.institution_name:
                raise ValueError("Institution name cannot be empty")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date")
        return self


class EducationResponse(BaseModel):
    """Response schema for Education entity."""

    id: UUID
    profile_id: UUID
    institution_name: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
