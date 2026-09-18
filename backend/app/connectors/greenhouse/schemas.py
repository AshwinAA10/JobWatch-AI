"""Pydantic schemas for Greenhouse job board API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GreenhouseLocation(BaseModel):
    """Greenhouse job location structure."""

    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None


class GreenhouseDepartment(BaseModel):
    """Greenhouse department metadata."""

    model_config = ConfigDict(extra="ignore")
    id: Optional[int] = None
    name: Optional[str] = None


class GreenhouseMetadata(BaseModel):
    """Greenhouse custom question or metadata field."""

    model_config = ConfigDict(extra="ignore")
    id: Optional[int] = None
    name: Optional[str] = None
    value: Optional[Any] = None
    value_type: Optional[str] = None


class GreenhouseJob(BaseModel):
    """Greenhouse single job posting record."""

    model_config = ConfigDict(extra="ignore")

    id: Any
    title: str
    updated_at: Optional[datetime] = None
    absolute_url: str
    location: Optional[GreenhouseLocation] = None
    content: Optional[str] = None
    departments: Optional[List[GreenhouseDepartment]] = None
    metadata: Optional[List[GreenhouseMetadata]] = None


class GreenhouseJobsResponse(BaseModel):
    """Greenhouse jobs list endpoint response."""

    model_config = ConfigDict(extra="ignore")
    jobs: List[GreenhouseJob] = Field(default_factory=list)
