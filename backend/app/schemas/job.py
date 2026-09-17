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
