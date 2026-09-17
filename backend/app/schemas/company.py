"""Pydantic schemas for Company entity."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    """Base attributes for a company."""

    name: str = Field(..., max_length=255, description="Organization legal or operating name")
    slug: str = Field(..., max_length=255, description="URL-safe unique identifier")
    website_url: Optional[str] = Field(None, max_length=2048, description="Primary corporate website URL")
    description: Optional[str] = Field(None, description="Brief description of the organization")
    is_active: bool = Field(True, description="Whether monitoring for this company is active")


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    pass


class CompanyRead(CompanyBase):
    """Schema for returning company details."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
