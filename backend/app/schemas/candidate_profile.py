"""Pydantic schemas for CandidateProfile entity."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import ProfileVisibility
from app.schemas.candidate_preferences import CandidatePreferencesResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.skill import CandidateSkillResponse


class CandidateProfileCreate(BaseModel):
    """Payload to initialize a candidate profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    years_of_experience: Optional[float] = None
    current_job_title: Optional[str] = None
    current_company: Optional[str] = None
    highest_education_level: Optional[str] = None
    profile_visibility: ProfileVisibility = ProfileVisibility.PRIVATE

    @field_validator("years_of_experience")
    @classmethod
    def validate_experience(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Years of experience cannot be negative")
        return v


class CandidateProfileUpdate(BaseModel):
    """Payload to update an existing candidate profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    years_of_experience: Optional[float] = None
    current_job_title: Optional[str] = None
    current_company: Optional[str] = None
    highest_education_level: Optional[str] = None
    profile_visibility: Optional[ProfileVisibility] = None

    @field_validator("years_of_experience")
    @classmethod
    def validate_experience(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Years of experience cannot be negative")
        return v


class CandidateProfileResponse(BaseModel):
    """Basic response schema for CandidateProfile."""

    id: UUID
    user_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    years_of_experience: Optional[float] = None
    current_job_title: Optional[str] = None
    current_company: Optional[str] = None
    highest_education_level: Optional[str] = None
    profile_visibility: ProfileVisibility
    profile_completion_percent: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateProfileDetailResponse(CandidateProfileResponse):
    """Comprehensive candidate profile with all child entities."""

    skills: List[CandidateSkillResponse] = []
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []
    preferences: Optional[CandidatePreferencesResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileCompletenessResponse(BaseModel):
    """Detailed profile completeness breakdown."""

    profile_completion_percent: int
    missing_sections: List[str]
    breakdown: Dict[str, bool]
