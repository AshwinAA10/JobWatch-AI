"""Domain models and data structures for the deterministic matching engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


class DimensionStatus(str, Enum):
    """Evaluation status for a single matching dimension."""

    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class DimensionResult:
    """Outcome of evaluating an individual matching dimension."""

    dimension: str
    score: Optional[float]  # 0.0 - 100.0 or None if UNKNOWN/NOT_APPLICABLE
    status: DimensionStatus
    matched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    mismatches: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "score": round(self.score, 1) if self.score is not None else None,
            "status": self.status.value,
            "matched": self.matched,
            "missing": self.missing,
            "mismatches": self.mismatches,
            "reasons": self.reasons,
            "metadata": self.metadata,
        }


@dataclass
class CandidateMatchFeatures:
    """Extracted features from a CandidateProfile for matching."""

    profile_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None

    # Skills (normalized lowercase canonical names)
    skills: Set[str] = field(default_factory=set)
    skill_experience: Dict[str, float] = field(default_factory=dict)

    # Experience
    total_experience_years: Optional[float] = None
    calculated_experience_years: float = 0.0

    # Titles
    current_title: Optional[str] = None
    desired_titles: List[str] = field(default_factory=list)

    # Location & Relocation
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    preferred_locations: List[str] = field(default_factory=list)
    willing_to_relocate: bool = False
    remote_preference: Optional[str] = None

    # Workplace & Employment preferences
    workplace_types: List[str] = field(default_factory=list)
    employment_types: List[str] = field(default_factory=list)

    # Compensation
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: str = "USD"

    # Education
    highest_education_level: Optional[str] = None
    degrees: List[str] = field(default_factory=list)


@dataclass
class JobMatchFeatures:
    """Extracted features from a Job and JobRequirements for matching."""

    job_id: uuid.UUID
    title: str

    # Direct Job attributes
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None

    # Structured Requirements (from JobRequirements if available)
    has_requirements: bool = False
    required_skills: Set[str] = field(default_factory=set)
    preferred_skills: Set[str] = field(default_factory=set)
    minimum_experience_years: Optional[float] = None
    maximum_experience_years: Optional[float] = None
    minimum_salary: Optional[int] = None
    maximum_salary: Optional[int] = None
    salary_currency: Optional[str] = None
    required_education_level: Optional[str] = None


@dataclass
class MatchResult:
    """Complete result of a deterministic matching evaluation."""

    job_id: uuid.UUID
    profile_id: uuid.UUID
    score: float  # 0.0 - 100.0 rounded
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    scoring_version: str
    breakdown: Dict[str, Any]
    matched_criteria: List[str] = field(default_factory=list)
    missing_criteria: List[str] = field(default_factory=list)
    mismatches: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict representation for API and persistence."""
        return {
            "job_id": str(self.job_id),
            "profile_id": str(self.profile_id),
            "score": self.score,
            "confidence": self.confidence,
            "scoring_version": self.scoring_version,
            "breakdown": self.breakdown,
            "matched_criteria": self.matched_criteria,
            "missing_criteria": self.missing_criteria,
            "mismatches": self.mismatches,
            "reasons": self.reasons,
            "metadata": self.metadata,
        }
