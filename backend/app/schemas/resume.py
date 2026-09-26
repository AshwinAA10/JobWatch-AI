"""Pydantic schemas for Resume entity."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ResumeCreate(BaseModel):
    """Payload to register resume metadata."""

    filename: str
    content_type: str
    storage_key: str
    file_size: int


class ResumeResponse(BaseModel):
    """Response schema for Resume metadata."""

    id: UUID
    profile_id: UUID
    filename: str
    content_type: str
    storage_key: str
    file_size: int
    uploaded_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
