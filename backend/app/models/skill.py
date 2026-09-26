"""Skill entity representing normalized professional capabilities."""

from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_skill import CandidateSkill


class Skill(Base, TimestampMixin):
    """Represents a canonical skill or capability that candidates can possess."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Relationship to candidate skill associations
    candidate_skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', normalized_name='{self.normalized_name}')>"
