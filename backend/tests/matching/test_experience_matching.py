"""Unit tests for deterministic experience matching dimension."""

import uuid
from app.matching.models import CandidateMatchFeatures, DimensionStatus, JobMatchFeatures
from app.matching.rules import evaluate_experience


def test_experience_meets_minimum_exactly():
    """Candidate experience equals job minimum."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=3.0,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Mid Engineer",
        minimum_experience_years=3.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.MATCH
    assert result.score == 100.0
    assert len(result.matched) > 0


def test_experience_exceeds_minimum():
    """Candidate experience exceeds minimum requirement."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=5.5,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Junior Developer",
        minimum_experience_years=2.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.MATCH
    assert result.score == 100.0


def test_experience_below_minimum_slight_gap():
    """Candidate has 2.5 years for 3.0 years requirement (ratio >= 0.7)."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=2.5,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Mid Engineer",
        minimum_experience_years=3.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.PARTIAL
    assert result.score == 70.0
    assert len(result.missing) > 0


def test_experience_below_minimum_severe_gap():
    """Candidate has 0.5 years for 5.0 years requirement."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=0.5,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Senior Architect",
        minimum_experience_years=5.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.MISMATCH
    assert result.score == 15.0
    assert len(result.mismatches) > 0


def test_experience_no_job_requirement():
    """Job specifies neither minimum nor maximum experience."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=4.0,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Open Role",
        minimum_experience_years=None,
        maximum_experience_years=None,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.NOT_APPLICABLE
    assert result.score is None


def test_experience_missing_candidate_experience():
    """Candidate has not specified experience years."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=None,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Role with Exp",
        minimum_experience_years=3.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.status == DimensionStatus.UNKNOWN
    assert result.score is None


def test_experience_exceeds_maximum_conservatively():
    """Candidate experience greatly exceeds maximum experience (conservative penalty)."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        total_experience_years=12.0,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Junior Developer",
        minimum_experience_years=1.0,
        maximum_experience_years=3.0,
    )
    result = evaluate_experience(candidate, job)
    assert result.score == 80.0
    assert "exceeds preferred maximum" in result.reasons[1]
