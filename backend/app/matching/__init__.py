"""JobWatch AI Deterministic Matching Engine package (Phase 6)."""

from app.matching.constants import (
    DEFAULT_MATCH_WEIGHTS,
    EDUCATION_HIERARCHY,
    SCORING_VERSION,
    SKILL_ALIASES,
    TITLE_ALIASES,
)
from app.matching.engine import MatchingEngine
from app.matching.features import (
    calculate_experience_years_from_history,
    extract_candidate_features,
    extract_job_features,
    normalize_skill,
    normalize_title,
)
from app.matching.models import (
    CandidateMatchFeatures,
    DimensionResult,
    DimensionStatus,
    JobMatchFeatures,
    MatchResult,
)

__all__ = [
    "MatchingEngine",
    "CandidateMatchFeatures",
    "JobMatchFeatures",
    "DimensionResult",
    "DimensionStatus",
    "MatchResult",
    "DEFAULT_MATCH_WEIGHTS",
    "SCORING_VERSION",
    "SKILL_ALIASES",
    "TITLE_ALIASES",
    "EDUCATION_HIERARCHY",
    "extract_candidate_features",
    "extract_job_features",
    "normalize_skill",
    "normalize_title",
    "calculate_experience_years_from_history",
]
