"""ApplicationNote entity representing candidate notes attached to a job application."""

from typing import TYPE_CHECKING
import uuid
from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.application import Application


class ApplicationNote(Base, TimestampMixin):
    """Candidate-authored notes and reminders on an application."""

    __tablename__ = "application_notes"
    __table_args__ = (
        Index("ix_application_notes_application_id", "application_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="application_notes",
    )

    def __repr__(self) -> str:
        return f"<ApplicationNote(id={self.id}, application_id={self.application_id})>"
