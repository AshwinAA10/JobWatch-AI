"""Repository for Interview entity persistence and queries."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import Interview


class InterviewRepository:
    """Data access repository for Interview."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        application_id: UUID,
        interview_type: str,
        status: str,
        scheduled_at: datetime,
        duration_minutes: Optional[int] = None,
        interviewer_names: Optional[str] = None,
        location: Optional[str] = None,
        meeting_url: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Interview:
        """Create and persist a new Interview record."""
        interview = Interview(
            application_id=application_id,
            interview_type=interview_type,
            status=status,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            interviewer_names=interviewer_names,
            location=location,
            meeting_url=meeting_url,
            notes=notes,
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def get_by_id(self, interview_id: UUID) -> Optional[Interview]:
        """Fetch an Interview by primary key."""
        return self.db.get(Interview, interview_id)

    def list_for_application(self, application_id: UUID) -> List[Interview]:
        """Retrieve interviews for an application ordered by scheduled date ascending."""
        stmt = (
            select(Interview)
            .where(Interview.application_id == application_id)
            .order_by(Interview.scheduled_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def update(
        self,
        interview: Interview,
        **kwargs,
    ) -> Interview:
        """Update mutable fields on an Interview instance."""
        for field, value in kwargs.items():
            if hasattr(interview, field) and value is not None:
                setattr(interview, field, value)

        self.db.commit()
        self.db.refresh(interview)
        return interview

    def delete(self, interview: Interview) -> None:
        """Delete an Interview record."""
        self.db.delete(interview)
        self.db.commit()
