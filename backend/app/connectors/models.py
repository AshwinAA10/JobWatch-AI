"""Normalized job models and provider-agnostic ingestion contracts."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NormalizedJob(BaseModel):
    """Provider-independent canonical job representation.
    
    All career portal connectors must transform raw third-party job data
    into this normalized format before passing it to the ingestion service.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    external_id: str = Field(
        ...,
        description="Unique identifier assigned by external ATS/career platform",
    )
    title: str = Field(
        ...,
        description="Normalized job title",
    )
    description: Optional[str] = Field(
        None,
        description="Job description text or cleaned HTML",
    )
    location: Optional[str] = Field(
        None,
        description="Normalized geographic location or remote designation",
    )
    employment_type: Optional[str] = Field(
        None,
        description="Standardized employment type: full_time, part_time, contract, internship",
    )
    workplace_type: Optional[str] = Field(
        None,
        description="Standardized workplace model: remote, hybrid, onsite",
    )
    application_url: str = Field(
        ...,
        description="Direct application or submission URL",
    )
    source_url: Optional[str] = Field(
        None,
        description="Original public posting or portal URL",
    )
    posted_at: Optional[datetime] = Field(
        None,
        description="Timestamp when opportunity was first published externally (UTC)",
    )
    raw_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional sanitized provider metadata for debugging or downstream enrichment",
    )
