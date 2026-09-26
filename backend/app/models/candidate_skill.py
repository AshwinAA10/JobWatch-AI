"""CandidateSkill association entity linking CandidateProfile and Skill."""

from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.enums import ProficiencyLevel

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.skill import Skill


class CandidateSkill(Base, TimestampMixin):
    """Associates a candidate profile with a specific skill, including proficiency and experience."""

    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "skill_id",
            name="uq_candidate_skills_profile_skill",
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
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proficiency: Mapped[str] = mapped_column(
        String(32),
        default=ProficiencyLevel.INTERMEDIATE.value,
        nullable=False,
    )
    years_experience: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Relationships
    profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile",
        back_populates="skills",
    )
    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="candidate_skills",
    )

    def __repr__(self) -> str:
        return f"<CandidateSkill(profile_id={self.profile_id}, skill_id={self.skill_id}, proficiency='{self.proficiency}')>"
