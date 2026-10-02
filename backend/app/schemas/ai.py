"""Pydantic schemas for Phase 7 AI intelligence and enhanced matching responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class AIJobRequirements(BaseModel):
    """Schema-constrained structured output for AI job description extraction."""

    required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory technical and domain skills explicitly required by the job posting",
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred, bonus, or nice-to-have skills explicitly mentioned",
    )
    minimum_experience_years: Optional[float] = Field(
        None,
        description="Minimum years of relevant experience explicitly required. Null if not specified.",
    )
    maximum_experience_years: Optional[float] = Field(
        None,
        description="Maximum or target years of experience if mentioned. Null if not specified.",
    )
    workplace_type: Optional[str] = Field(
        None,
        description="Explicit workplace arrangement: REMOTE, HYBRID, or ONSITE. Null if unknown.",
    )
    employment_type: Optional[str] = Field(
        None,
        description="Explicit employment classification: FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, or TEMPORARY. Null if unknown.",
    )
    locations: List[str] = Field(
        default_factory=list,
        description="Locations, cities, states, or countries where the role is based.",
    )
    minimum_salary: Optional[int] = Field(
        None,
        description="Annual minimum salary if explicitly provided in the text. Null if not specified.",
    )
    maximum_salary: Optional[int] = Field(
        None,
        description="Annual maximum salary if explicitly provided in the text. Null if not specified.",
    )
    salary_currency: Optional[str] = Field(
        None,
        description="ISO 3-letter currency code (e.g., USD, EUR, INR) if salary is mentioned. Null otherwise.",
    )
    required_education_level: Optional[str] = Field(
        None,
        description="Minimum degree level (e.g., High School, Associate, Bachelor's, Master's, Doctorate) if explicitly required.",
    )
    role_keywords: List[str] = Field(
        default_factory=list,
        description="Primary technical domain keywords describing the position.",
    )
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Summary of key core job responsibilities explicitly listed.",
    )


class JobExtractionResponse(BaseModel):
    """Response representation of AI job requirements extraction."""

    job_id: UUID
    input_hash: str
    model: str
    prompt_version: str
    extraction_version: str
    is_success: bool
    error_message: Optional[str] = None
    structured_requirements: Optional[AIJobRequirements] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIExplanationResponse(BaseModel):
    """Structured narrative match explanation response."""

    summary: str
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendation: str


class EnhancedMatchResponse(BaseModel):
    """Complete response for AI-enhanced hybrid matching."""

    job_id: UUID
    profile_id: UUID
    deterministic_score: float
    semantic_score: Optional[float] = None
    hybrid_score: float
    scoring_version: str = "v1"
    ai_status: str  # AI_AVAILABLE, AI_PARTIAL, AI_UNAVAILABLE, DISABLED, etc.
    embedding_model: Optional[str] = None
    guardrail_applied: bool = False
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    semantic_details: Optional[Dict[str, Any]] = None
    matched_criteria: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)
    mismatches: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    explanation: Optional[AIExplanationResponse] = None
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillGapResponse(BaseModel):
    """Structured breakdown of candidate skills vs job requirements with ontology insights."""

    job_id: UUID
    profile_id: UUID
    matched_required: List[str] = Field(default_factory=list)
    matched_preferred: List[str] = Field(default_factory=list)
    transferable_matches: List[Dict[str, Any]] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    missing_preferred: List[str] = Field(default_factory=list)
    required_coverage: float = 1.0


class SemanticSearchResult(BaseModel):
    """Individual item returned in a semantic natural language query search."""

    job_id: UUID
    title: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    semantic_similarity: float
    relevance_score: float


class SimilarJobItem(BaseModel):
    """Adjacent or similar job recommendation based on semantic vectors."""

    job_id: UUID
    title: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    workplace_type: Optional[str] = None
    similarity: float
    match_reason: str
