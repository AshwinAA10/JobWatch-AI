"""Unit tests for deterministic skill matching dimension."""

import uuid
from app.matching.features import normalize_skill
from app.matching.models import CandidateMatchFeatures, DimensionStatus, JobMatchFeatures
from app.matching.rules import evaluate_skills


def test_normalize_skill_aliases():
    """Verify deterministic skill normalization and canonical aliases."""
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("react") == "react"
    assert normalize_skill("Node.js") == "node.js"
    assert normalize_skill("NodeJS") == "node.js"
    assert normalize_skill("TS") == "typescript"
    assert normalize_skill("Python3") == "python"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill("UnknownSkillXYZ") == "unknownskillxyz"
    assert normalize_skill("") == ""
    assert normalize_skill(None) == ""


def test_skills_100_percent_required_match():
    """Candidate possesses all required skills."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"react", "typescript", "node.js", "docker"},
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Frontend Developer",
        required_skills={"react", "typescript"},
    )
    result = evaluate_skills(candidate, job)
    assert result.status == DimensionStatus.MATCH
    assert result.score == 100.0
    assert "react" in result.matched
    assert "typescript" in result.matched
    assert len(result.missing) == 0


def test_skills_partial_required_match():
    """Candidate has 1 of 2 required skills."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"react", "python"},
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Frontend Developer",
        required_skills={"react", "typescript"},
    )
    result = evaluate_skills(candidate, job)
    assert result.status == DimensionStatus.PARTIAL
    assert result.score == 50.0
    assert "react" in result.matched
    assert "typescript" in result.missing
    assert "typescript" in result.mismatches


def test_skills_no_required_match():
    """Candidate has zero required skills."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"python", "django"},
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Frontend Developer",
        required_skills={"react", "typescript"},
    )
    result = evaluate_skills(candidate, job)
    assert result.status == DimensionStatus.MISMATCH
    assert result.score == 0.0
    assert len(result.matched) == 0
    assert len(result.missing) == 2


def test_skills_required_and_preferred_weighted():
    """Candidate has all required skills (80%) and 1 of 2 preferred skills (10%)."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"react", "typescript", "docker"},
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Full Stack Developer",
        required_skills={"react", "typescript"},
        preferred_skills={"docker", "aws"},
    )
    result = evaluate_skills(candidate, job)
    # Required coverage: 1.0 * 0.8 = 0.8
    # Preferred coverage: 0.5 * 0.2 = 0.1
    # Total = 90.0
    assert result.status == DimensionStatus.MATCH
    assert result.score == 90.0
    assert "docker" in result.matched
    assert "aws" in result.missing


def test_skills_no_skill_requirements():
    """When a job specifies no skills, status is UNKNOWN with score None."""
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills={"react", "python"},
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="General Developer",
        required_skills=set(),
        preferred_skills=set(),
    )
    result = evaluate_skills(candidate, job)
    assert result.status == DimensionStatus.UNKNOWN
    assert result.score is None
    assert "No skill requirements specified" in result.reasons[0]


def test_skills_duplicate_and_casing_handling():
    """Duplicate candidate skills or case variations normalize deterministically."""
    candidate_skills = {normalize_skill(s) for s in ["React.js", "REACT", "reactjs"]}
    assert candidate_skills == {"react"}

    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        skills=candidate_skills,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="React Dev",
        required_skills={"react"},
    )
    result = evaluate_skills(candidate, job)
    assert result.status == DimensionStatus.MATCH
    assert result.score == 100.0
