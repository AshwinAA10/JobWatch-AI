"""Pydantic schemas for Application, ApplicationHistory, ApplicationNote, and Interview."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationStatus, InterviewStatus, InterviewType


# --- Application Note Schemas ---

class ApplicationNoteCreate(BaseModel):
    """Payload to add a candidate note to an application."""

    content: str = Field(..., min_length=1, max_length=10000, description="Content of the candidate note")


class ApplicationNoteUpdate(BaseModel):
    """Payload to edit a candidate note."""

    content: str = Field(..., min_length=1, max_length=10000, description="Updated content of the candidate note")


class ApplicationNoteResponse(BaseModel):
    """Schema for reading a candidate application note."""

    id: UUID
    application_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Interview Schemas ---

class InterviewCreate(BaseModel):
    """Payload to record a scheduled interview."""

    interview_type: InterviewType = Field(InterviewType.TECHNICAL, description="Type of interview round")
    status: InterviewStatus = Field(InterviewStatus.SCHEDULED, description="Status of the interview")
    scheduled_at: datetime = Field(..., description="Scheduled date and time in UTC")
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Duration in minutes")
    interviewer_names: Optional[str] = Field(None, max_length=255, description="Interviewer names or roles")
    location: Optional[str] = Field(None, max_length=255, description="Location or platform")
    meeting_url: Optional[str] = Field(None, max_length=2048, description="Meeting link URL")
    notes: Optional[str] = Field(None, max_length=10000, description="Prep notes or feedback")


class InterviewUpdate(BaseModel):
    """Payload to update an interview record."""

    interview_type: Optional[InterviewType] = None
    status: Optional[InterviewStatus] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    interviewer_names: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    meeting_url: Optional[str] = Field(None, max_length=2048)
    notes: Optional[str] = Field(None, max_length=10000)


class InterviewResponse(BaseModel):
    """Schema for reading interview details."""

    id: UUID
    application_id: UUID
    interview_type: str
    status: str
    scheduled_at: datetime
    duration_minutes: Optional[int] = None
    interviewer_names: Optional[str] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Application History Schemas ---

class ApplicationHistoryResponse(BaseModel):
    """Audit log entry representing a status transition."""

    id: UUID
    application_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_at: datetime
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Core Application Schemas ---

class ApplicationCreate(BaseModel):
    """Payload to create/track a new job application."""

    job_id: Optional[UUID] = Field(None, description="ID of canonical job if applied from catalog")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name (optional if job_id supplied)")
    job_title: Optional[str] = Field(None, max_length=512, description="Job title (optional if job_id supplied)")
    job_location: Optional[str] = Field(None, max_length=255, description="Location (optional)")
    external_application_url: Optional[str] = Field(None, max_length=2048, description="URL where application was submitted")
    applied_at: Optional[datetime] = Field(None, description="Timestamp when submitted (defaults to now)")
    notes: Optional[str] = Field(None, max_length=5000, description="Initial note or submission context")


class ApplicationUpdate(BaseModel):
    """Payload to edit mutable application details."""

    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=512)
    job_location: Optional[str] = Field(None, max_length=255)
    external_application_url: Optional[str] = Field(None, max_length=2048)
    notes: Optional[str] = Field(None, max_length=5000)


class ApplicationStatusUpdate(BaseModel):
    """Payload to transition application status with audit note."""

    status: ApplicationStatus = Field(..., description="Target lifecycle status")
    note: Optional[str] = Field(None, max_length=1000, description="Reason or context for status update")


class ApplicationListItem(BaseModel):
    """Summary item for application list queries."""

    id: UUID
    profile_id: UUID
    job_id: Optional[UUID] = None
    status: str
    applied_at: datetime
    last_status_changed_at: datetime
    company_name: str
    job_title: str
    job_location: Optional[str] = None
    external_application_url: Optional[str] = None
    match_score_at_application: Optional[float] = None
    notes_count: int = 0
    interviews_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    """Full detail schema for an application with child records."""

    id: UUID
    profile_id: UUID
    job_id: Optional[UUID] = None
    status: str
    applied_at: datetime
    last_status_changed_at: datetime
    company_name: str
    job_title: str
    job_location: Optional[str] = None
    external_application_url: Optional[str] = None
    match_score_at_application: Optional[float] = None
    notes: Optional[str] = None
    history: List[ApplicationHistoryResponse] = Field(default_factory=list)
    application_notes: List[ApplicationNoteResponse] = Field(default_factory=list)
    interviews: List[InterviewResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    """Paginated response schema for applications."""

    items: List[ApplicationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApplicationStatistics(BaseModel):
    """Candidate application lifecycle statistics."""

    total: int
    applied: int
    screening: int
    interview: int
    offer: int
    rejected: int
    withdrawn: int
    accepted: int
