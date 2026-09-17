"""Company database entity."""

from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.career_source import CareerSource
    from app.models.job import Job


class Company(Base, TimestampMixin):
    """Represents an employer or organization whose career opportunities are monitored."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    website_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Relationships
    career_sources: Mapped[List["CareerSource"]] = relationship(
        "CareerSource",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', slug='{self.slug}')>"
