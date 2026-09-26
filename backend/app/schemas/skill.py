"""Pydantic schemas for Skill and CandidateSkill entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import ProficiencyLevel


class SkillCreate(BaseModel):
    """Payload to create a new canonical skill."""

    name: str
    category: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Skill name cannot be empty")
        if len(v) > 100:
            raise ValueError("Skill name cannot exceed 100 characters")
        return v


class SkillResponse(BaseModel):
    """Response schema for canonical skill."""

    id: UUID
    name: str
    normalized_name: str
    category: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateSkillCreate(BaseModel):
    """Payload to attach a skill to a candidate profile."""

    skill_name: Optional[str] = None
    skill_id: Optional[UUID] = None
    proficiency: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    years_experience: Optional[float] = None

    @field_validator("years_experience")
    @classmethod
    def validate_years(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Years of experience cannot be negative")
        return v

    @field_validator("skill_name")
    @classmethod
    def clean_skill_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class CandidateSkillUpdate(BaseModel):
    """Payload to update an existing candidate skill association."""

    proficiency: Optional[ProficiencyLevel] = None
    years_experience: Optional[float] = None

    @field_validator("years_experience")
    @classmethod
    def validate_years(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Years of experience cannot be negative")
        return v


class CandidateSkillResponse(BaseModel):
    """Response schema for candidate-skill association."""

    id: UUID
    profile_id: UUID
    skill_id: UUID
    skill: SkillResponse
    proficiency: ProficiencyLevel
    years_experience: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
