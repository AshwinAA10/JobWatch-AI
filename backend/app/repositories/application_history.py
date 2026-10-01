"""Repository for ApplicationHistory audit record queries."""

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_history import ApplicationHistory


class ApplicationHistoryRepository:
    """Data access repository for ApplicationHistory."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_application(self, application_id: UUID) -> List[ApplicationHistory]:
        """Fetch chronologically ordered history transitions for an application."""
        stmt = (
            select(ApplicationHistory)
            .where(ApplicationHistory.application_id == application_id)
            .order_by(ApplicationHistory.changed_at.asc(), ApplicationHistory.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())
