"""ApplicationHistory entity recording audit log of application status transitions."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.application import Application


class ApplicationHistory(Base, TimestampMixin):
    """Immutable audit entry for each lifecycle status transition of an application."""

    __tablename__ = "application_history"
    __table_args__ = (
        Index("ix_application_history_application_id", "application_id"),
        Index("ix_application_history_changed_at", "changed_at"),
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

    old_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )
    new_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="history",
    )

    def __repr__(self) -> str:
        return f"<ApplicationHistory(id={self.id}, application_id={self.application_id}, {self.old_status} -> {self.new_status})>"
