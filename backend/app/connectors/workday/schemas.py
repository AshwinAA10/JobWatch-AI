"""Pydantic schemas for Workday Candidate Experience (CXS) API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkdayJobPosting(BaseModel):
    """Workday single job listing from search results."""

    model_config = ConfigDict(extra="ignore")

    title: str
    externalPath: str
    bulletFields: Optional[List[str]] = None
    locationsText: Optional[str] = None
    postedOn: Optional[str] = None
    timeType: Optional[str] = None  # e.g., "Full time", "Part time"
    subdomain: Optional[str] = None


class WorkdaySearchResponse(BaseModel):
    """Workday search results response schema."""

    model_config = ConfigDict(extra="ignore")

    total: int = 0
    limit: int = 20
    offset: int = 0
    jobPostings: List[WorkdayJobPosting] = Field(default_factory=list)
