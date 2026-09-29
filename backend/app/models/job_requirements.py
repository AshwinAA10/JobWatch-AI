"""JobRequirements database entity capturing structured role criteria."""

from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job


class JobRequirements(Base, TimestampMixin):
    """Structured requirements and qualifications associated with a Job."""

    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Required & Preferred Skills
    required_skills: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    preferred_skills: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Experience Bounds (in years)
    minimum_experience_years: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    maximum_experience_years: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Compensation Expectations
    minimum_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    maximum_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    salary_currency: Mapped[Optional[str]] = mapped_column(
        String(3),
        default="USD",
        nullable=True,
    )

    # Academic Criteria
    required_education_level: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationship to Job
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="requirements",
    )

    def __repr__(self) -> str:
        return f"<JobRequirements(job_id={self.job_id}, min_exp={self.minimum_experience_years})>"
