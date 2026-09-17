"""Pydantic schemas for CareerSource entity."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CareerSourceBase(BaseModel):
    """Base attributes for a career source."""

    company_id: UUID = Field(..., description="ID of the parent company")
    name: str = Field(..., max_length=255, description="Name of the career source or portal")
    source_type: str = Field(..., max_length=64, description="Type of ATS or portal (e.g., greenhouse, lever, workday)")
    base_url: str = Field(..., max_length=2048, description="Target base URL of the portal")
    is_active: bool = Field(True, description="Whether this source is currently being crawled")


class CareerSourceCreate(CareerSourceBase):
    """Schema for creating a career source."""
    pass


class CareerSourceRead(CareerSourceBase):
    """Schema for reading career source details."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
