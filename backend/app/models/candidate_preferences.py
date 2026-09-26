"""CandidatePreferences entity capturing job criteria and preferences."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile


class CandidatePreferences(Base, TimestampMixin):
    """Structured job preferences and target criteria for a candidate."""

    __tablename__ = "candidate_preferences"
    __table_args__ = (
        CheckConstraint(
            "minimum_salary IS NULL OR maximum_salary IS NULL OR maximum_salary >= minimum_salary",
            name="ck_preferences_salary_range",
        ),
        CheckConstraint(
            "minimum_experience_years IS NULL OR maximum_experience_years IS NULL OR maximum_experience_years >= minimum_experience_years",
            name="ck_preferences_experience_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Preferences collections stored as JSON arrays for flexible multi-value criteria
    desired_titles: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    preferred_locations: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    workplace_types: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )  # e.g., ["REMOTE", "HYBRID", "ONSITE"]
    employment_types: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )  # e.g., ["FULL_TIME", "CONTRACT"]

    # Compensation & Seniority Expectations
    minimum_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    maximum_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    salary_currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    minimum_experience_years: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    maximum_experience_years: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Mobility & Remote Preferences
    willing_to_relocate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    remote_preference: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    # Relationships
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="preferences",
    )

    def __repr__(self) -> str:
        return f"<CandidatePreferences(profile_id={self.profile_id}, currency='{self.salary_currency}')>"
