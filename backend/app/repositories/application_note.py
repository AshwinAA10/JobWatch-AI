"""Repository for ApplicationNote entity persistence and queries."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_note import ApplicationNote


class ApplicationNoteRepository:
    """Data access repository for ApplicationNote."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, application_id: UUID, content: str) -> ApplicationNote:
        """Create and persist a new ApplicationNote."""
        note = ApplicationNote(
            application_id=application_id,
            content=content,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_by_id(self, note_id: UUID) -> Optional[ApplicationNote]:
        """Fetch an ApplicationNote by primary key."""
        return self.db.get(ApplicationNote, note_id)

    def list_for_application(self, application_id: UUID) -> List[ApplicationNote]:
        """Retrieve notes for an application ordered by creation date descending."""
        stmt = (
            select(ApplicationNote)
            .where(ApplicationNote.application_id == application_id)
            .order_by(ApplicationNote.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, note: ApplicationNote, content: str) -> ApplicationNote:
        """Update content of an existing note."""
        note.content = content
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete(self, note: ApplicationNote) -> None:
        """Delete an ApplicationNote."""
        self.db.delete(note)
        self.db.commit()
