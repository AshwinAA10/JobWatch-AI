"""Pydantic schemas for Job entity."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    """Base attributes for a job opening."""

    company_id: UUID = Field(..., description="ID of the parent company")
    career_source_id: UUID = Field(..., description="ID of the career source")
    external_id: Optional[str] = Field(None, max_length=255, description="External ATS/portal identifier")
    title: str = Field(..., max_length=512, description="Job title")
    description: Optional[str] = Field(None, description="Raw or formatted job description")
    location: Optional[str] = Field(None, max_length=255, description="Primary location")
    employment_type: Optional[str] = Field(None, max_length=64, description="Employment type (full-time, etc.)")
    workplace_type: Optional[str] = Field(None, max_length=64, description="Workplace type (remote, hybrid, on-site)")
    application_url: Optional[str] = Field(None, max_length=2048, description="Direct URL to apply")
    source_url: Optional[str] = Field(None, max_length=2048, description="Original URL where posting was found")
    posted_at: Optional[datetime] = Field(None, description="When the position was externally posted")
    is_active: bool = Field(True, description="Whether the job is currently open")


class JobCreate(JobBase):
    """Schema for creating a new job posting."""
    pass


class JobRead(JobBase):
    """Schema for reading job details."""

    id: UUID
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCardResponse(BaseModel):
    """Card representation of a job opening for discovery and list views."""

    id: UUID
    company_id: UUID
    company_name: str
    company_slug: str
    career_source_name: Optional[str] = None
    title: str
    location: Optional[str] = None
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    application_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    first_seen_at: datetime
    canonical_job_id: Optional[UUID] = None
    is_active: bool = True
    match_score: Optional[float] = None
    match_confidence: Optional[str] = None
    match_type: Optional[str] = None
    match_reasons: list[str] = Field(default_factory=list)
    is_saved: bool = False
    application_id: Optional[UUID] = None
    application_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobCardResponse):
    """Full detail representation of a job opening including requirements and insights."""

    description: Optional[str] = None
    source_url: Optional[str] = None
    matched_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    breakdown: Optional[dict] = None
    ai_explanation: Optional[dict] = None
    structured_requirements: Optional[dict] = None
    duplicate_count: int = 0


class JobListResponse(BaseModel):
    """Paginated response for job search and discovery."""

    items: list[JobCardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SavedJobResponse(BaseModel):
    """Candidate saved/bookmarked job item."""

    id: UUID
    profile_id: UUID
    job_id: UUID
    notes: Optional[str] = None
    created_at: datetime
    job: JobCardResponse

    model_config = ConfigDict(from_attributes=True)

