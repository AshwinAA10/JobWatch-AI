"""Unit tests for weighted scoring, missing data normalization, and determinism."""

import uuid
import pytest
from app.matching.constants import DEFAULT_MATCH_WEIGHTS, SCORING_VERSION
from app.matching.engine import MatchingEngine
from app.matching.models import (
    CandidateMatchFeatures,
    DimensionResult,
    DimensionStatus,
    JobMatchFeatures,
)
from app.matching.scoring import calculate_weighted_score, validate_weights


def test_default_weights_sum_to_one():
    """Verify that default weights configuration strictly sums to 1.0."""
    assert validate_weights(DEFAULT_MATCH_WEIGHTS)
    assert abs(sum(DEFAULT_MATCH_WEIGHTS.values()) - 1.0) < 1e-6


def test_invalid_weights_rejected():
    """Engine initialization raises ValueError if weights do not sum to 1.0."""
    bad_weights = {"skills": 0.5, "experience": 0.2}
    with pytest.raises(ValueError):
        MatchingEngine(weights=bad_weights)


def test_missing_data_dynamic_normalization():
    """Missing/unknown dimensions are removed from denominator and do not penalize score."""
    # Suppose candidate and job only have skills and workplace type:
    # Skills = 100.0 (weight 0.35)
    # Workplace = 100.0 (weight 0.10)
    # All other dimensions are UNKNOWN/NOT_APPLICABLE with score=None
    dim_results = {
        "skills": DimensionResult(dimension="skills", score=100.0, status=DimensionStatus.MATCH),
        "experience": DimensionResult(dimension="experience", score=None, status=DimensionStatus.NOT_APPLICABLE),
        "title": DimensionResult(dimension="title", score=None, status=DimensionStatus.UNKNOWN),
        "location": DimensionResult(dimension="location", score=None, status=DimensionStatus.UNKNOWN),
        "workplace": DimensionResult(dimension="workplace", score=100.0, status=DimensionStatus.MATCH),
        "employment_type": DimensionResult(dimension="employment_type", score=None, status=DimensionStatus.UNKNOWN),
        "salary": DimensionResult(dimension="salary", score=None, status=DimensionStatus.UNKNOWN),
        "education": DimensionResult(dimension="education", score=None, status=DimensionStatus.NOT_APPLICABLE),
    }

    score, confidence, contributions = calculate_weighted_score(dim_results)
    # Both available dimensions scored 100%, so normalized score must be 100.0, not penalized to 45.0!
    assert score == 100.0
    assert confidence == "MEDIUM"  # 0.35 + 0.10 = 0.45 weight available


def test_engine_determinism():
    """Identical candidate and job match features evaluate to exact same result on every run."""
    engine = MatchingEngine()
    profile_id = uuid.uuid4()
    job_id = uuid.uuid4()

    candidate = CandidateMatchFeatures(
        profile_id=profile_id,
        skills={"react", "typescript", "python"},
        total_experience_years=4.0,
        desired_titles=["software engineer"],
        city="Coimbatore",
        preferred_locations=["Coimbatore", "Chennai"],
        willing_to_relocate=True,
        workplace_types=["REMOTE", "HYBRID"],
        employment_types=["FULL_TIME"],
        minimum_salary=80000,
        maximum_salary=110000,
        highest_education_level="Bachelor's",
    )

    job = JobMatchFeatures(
        job_id=job_id,
        title="Software Developer",
        required_skills={"react", "typescript"},
        preferred_skills={"docker"},
        minimum_experience_years=3.0,
        location="Coimbatore",
        workplace_type="HYBRID",
        employment_type="FULL_TIME",
        minimum_salary=90000,
        maximum_salary=120000,
        required_education_level="Bachelor's",
    )

    runs = [engine.match(candidate, job) for _ in range(5)]

    first_score = runs[0].score
    first_breakdown = runs[0].breakdown
    first_reasons = runs[0].reasons

    for idx, run in enumerate(runs[1:], start=2):
        assert run.score == first_score, f"Run {idx} score deviated"
        assert run.confidence == runs[0].confidence
        assert run.scoring_version == SCORING_VERSION
        assert run.breakdown == first_breakdown, f"Run {idx} breakdown deviated"
        assert run.reasons == first_reasons, f"Run {idx} reasons deviated"
        assert run.matched_criteria == runs[0].matched_criteria
        assert run.missing_criteria == runs[0].missing_criteria
        assert run.mismatches == runs[0].mismatches


def test_explanation_consistency():
    """Reasons generated strictly reflect evaluated dimensions without hallucination."""
    engine = MatchingEngine()
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"python"},
        desired_titles=["Backend Engineer"],
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Backend Engineer",
        required_skills={"python", "go"},
    )

    result = engine.match(candidate, job)
    # Check that reasons reflect matching python and missing go
    reasons_str = " ".join(result.reasons)
    assert "Matched 1 of 2 required skills" in reasons_str
    assert "Job title aligns strongly" in reasons_str
    # Must NOT hallucinate remote workplace when workplace wasn't specified
    assert "Job is fully remote" not in reasons_str
