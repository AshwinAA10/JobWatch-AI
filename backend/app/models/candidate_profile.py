"""CandidateProfile entity representing a user's professional identity."""

from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.enums import ProfileVisibility

if TYPE_CHECKING:
    from app.models.candidate_preferences import CandidatePreferences
    from app.models.candidate_skill import CandidateSkill
    from app.models.education import Education
    from app.models.experience import Experience
    from app.models.resume import Resume
    from app.models.user import User


class CandidateProfile(Base, TimestampMixin):
    """Core profile entity holding professional details, background, and relationships."""

    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Basic Contact & Personal Information
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    headline: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    # Location Information
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Professional Summary
    years_of_experience: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    current_job_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    current_company: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    highest_education_level: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Profile Settings & Completeness Metric
    profile_visibility: Mapped[str] = mapped_column(
        String(32),
        default=ProfileVisibility.PRIVATE.value,
        nullable=False,
    )
    profile_completion_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="candidate_profile",
    )
    skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(Experience.start_date)",
    )
    educations: Mapped[List["Education"]] = relationship(
        "Education",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(Education.start_date)",
    )
    preferences: Mapped[Optional["CandidatePreferences"]] = relationship(
        "CandidatePreferences",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CandidateProfile(id={self.id}, user_id={self.user_id}, name='{self.first_name} {self.last_name}')>"
