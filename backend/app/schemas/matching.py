"""Pydantic schemas for matching operations, requirements, and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class JobRequirementsBase(BaseModel):
    """Base schema for structured job requirements."""

    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    minimum_experience_years: Optional[float] = None
    maximum_experience_years: Optional[float] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: Optional[str] = "USD"
    required_education_level: Optional[str] = None


class JobRequirementsCreate(JobRequirementsBase):
    """Payload to create or set job requirements."""

    pass


class JobRequirementsUpdate(BaseModel):
    """Payload to update job requirements."""

    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    minimum_experience_years: Optional[float] = None
    maximum_experience_years: Optional[float] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: Optional[str] = None
    required_education_level: Optional[str] = None


class JobRequirementsResponse(JobRequirementsBase):
    """Response representation of JobRequirements."""

    id: UUID
    job_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DimensionResultSchema(BaseModel):
    """Evaluation breakdown for a specific dimension."""

    score: Optional[float] = None
    status: str
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    mismatches: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobMatchResponse(BaseModel):
    """Response representation of a job match evaluation."""

    id: Optional[UUID] = None
    job_id: UUID
    profile_id: UUID
    score: float
    confidence: Optional[str] = None
    scoring_version: str = "v1"
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    matched_criteria: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)
    mismatches: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    calculated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
