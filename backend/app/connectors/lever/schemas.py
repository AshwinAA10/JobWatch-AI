"""Pydantic schemas for Lever Postings API responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LeverCategories(BaseModel):
    """Lever categorization metadata."""

    model_config = ConfigDict(extra="ignore")

    commitment: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    location: Optional[str] = None
    allLocations: Optional[List[str]] = None


class LeverPosting(BaseModel):
    """Lever single job posting record."""

    model_config = ConfigDict(extra="ignore")

    id: str
    text: str  # Job title
    createdAt: Optional[int] = None  # Milliseconds epoch
    hostedUrl: str
    applyUrl: Optional[str] = None
    description: Optional[str] = None
    descriptionPlain: Optional[str] = None
    additional: Optional[str] = None
    additionalPlain: Optional[str] = None
    workplaceType: Optional[str] = None
    categories: Optional[LeverCategories] = None
    country: Optional[str] = None
