"""CareerSource database entity."""

from typing import TYPE_CHECKING, List
import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.job import Job


class CareerSource(Base, TimestampMixin):
    """Represents a career portal, ATS, or job page belonging to a company."""

    __tablename__ = "career_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )  # e.g., 'greenhouse', 'lever', 'workday', 'custom_html', 'custom_api'
    base_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="career_sources",
    )
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="career_source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CareerSource(id={self.id}, name='{self.name}', source_type='{self.source_type}')>"
