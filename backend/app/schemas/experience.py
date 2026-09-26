"""Pydantic schemas for Experience entity."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator


class ExperienceCreate(BaseModel):
    """Payload to add a work experience record."""

    company_name: str
    job_title: str
    description: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceCreate":
        self.company_name = self.company_name.strip()
        self.job_title = self.job_title.strip()
        if not self.company_name:
            raise ValueError("Company name cannot be empty")
        if not self.job_title:
            raise ValueError("Job title cannot be empty")
        if self.is_current:
            self.end_date = None
        elif self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date")
        return self


class ExperienceUpdate(BaseModel):
    """Payload to update an existing work experience record."""

    company_name: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

    @model_validator(mode="after")
    def validate_updates(self) -> "ExperienceUpdate":
        if self.company_name is not None:
            self.company_name = self.company_name.strip()
            if not self.company_name:
                raise ValueError("Company name cannot be empty")
        if self.job_title is not None:
            self.job_title = self.job_title.strip()
            if not self.job_title:
                raise ValueError("Job title cannot be empty")
        if self.is_current is True:
            self.end_date = None
        elif self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date")
        return self


class ExperienceResponse(BaseModel):
    """Response schema for Experience entity."""

    id: UUID
    profile_id: UUID
    company_name: str
    job_title: str
    description: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
