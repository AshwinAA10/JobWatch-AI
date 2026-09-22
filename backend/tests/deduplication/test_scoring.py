"""Unit tests for pairwise similarity scoring and false-positive prevention."""

import uuid
from app.deduplication.scoring import evaluate_job_pair
from app.models.job import Job
from app.models.job_duplicate import MatchType


def make_test_job(
    company_id: uuid.UUID,
    title: str,
    location: str = "Bengaluru, India",
    workplace_type: str = "remote",
    employment_type: str = "full-time",
    application_url: str = "https://boards.greenhouse.io/corp/jobs/101",
    source_url: str = "https://boards.greenhouse.io/corp/jobs/101",
    description: str = "Design, build, and deploy cloud infrastructure.",
    external_id: str = "ext-101",
) -> Job:
    """Helper to instantiate detached Job instances for scoring tests."""
    return Job(
        id=uuid.uuid4(),
        company_id=company_id,
        career_source_id=uuid.uuid4(),
        external_id=external_id,
        title=title,
        location=location,
        workplace_type=workplace_type,
        employment_type=employment_type,
        application_url=application_url,
        source_url=source_url,
        description=description,
    )


def test_hard_company_boundary():
    """Identical job attributes across different companies must NEVER be marked as duplicates."""
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()

    job_a = make_test_job(company_a, "Staff Backend Engineer")
    job_b = make_test_job(company_b, "Staff Backend Engineer")

    result = evaluate_job_pair(job_a, job_b)
    assert result.score == 0.0
    assert result.match_type == "DIFFERENT_COMPANY"
    assert "Different companies" in result.reason


def test_self_match_prevention():
    """Evaluating a job against itself returns score 0.0 and SELF_MATCH."""
    company_id = uuid.uuid4()
    job = make_test_job(company_id, "Senior Software Engineer")
    job.id = uuid.uuid4()

    result = evaluate_job_pair(job, job)
    assert result.score == 0.0
    assert result.match_type == "SELF_MATCH"


def test_exact_application_url_match():
    """Postings with identical canonical application URLs receive score 1.0."""
    company_id = uuid.uuid4()
    job_a = make_test_job(
        company_id,
        "Senior Backend Engineer",
        application_url="https://boards.greenhouse.io/stripe/jobs/101?utm_source=linkedin",
    )
    job_b = make_test_job(
        company_id,
        "Senior Backend Engineer - Core",
        application_url="https://boards.greenhouse.io/stripe/jobs/101?ref=jobboard",
    )

    result = evaluate_job_pair(job_a, job_b)
    assert result.score == 1.0
    assert result.match_type == MatchType.EXACT_APPLICATION_URL.value


def test_exact_source_url_match():
    """Postings with identical canonical source URLs receive score 0.98."""
    company_id = uuid.uuid4()
    job_a = make_test_job(
        company_id,
        "Senior Backend Engineer",
        application_url="https://app1.example.com/apply",
        source_url="https://jobs.lever.co/company/abc-123?utm_source=glassdoor",
    )
    job_b = make_test_job(
        company_id,
        "Senior Backend Engineer",
        application_url="https://app2.example.com/apply",
        source_url="https://jobs.lever.co/company/abc-123/",
    )

    result = evaluate_job_pair(job_a, job_b)
    assert result.score == 0.98
    assert result.match_type == MatchType.EXACT_SOURCE_URL.value


def test_seniority_contradiction_prevents_merge():
    """Senior vs Intern roles must never be considered duplicates despite title overlap."""
    company_id = uuid.uuid4()
    job_senior = make_test_job(
        company_id,
        "Senior Software Engineer",
        application_url="https://jobs.example.com/1",
        source_url="https://jobs.example.com/src1",
    )
    job_intern = make_test_job(
        company_id,
        "Software Engineering Intern",
        application_url="https://jobs.example.com/2",
        source_url="https://jobs.example.com/src2",
    )

    result = evaluate_job_pair(job_senior, job_intern)
    assert result.score <= 0.15
    assert result.match_type == "CONTRADICTION"


def test_physical_location_contradiction():
    """Distinct physical cities for on-site roles must strongly penalize score."""
    company_id = uuid.uuid4()
    job_london = make_test_job(
        company_id,
        "DevOps Engineer",
        location="London, United Kingdom",
        workplace_type="on-site",
        application_url="https://jobs.example.com/lon",
        source_url="https://jobs.example.com/srclon",
    )
    job_tokyo = make_test_job(
        company_id,
        "DevOps Engineer",
        location="Tokyo, Japan",
        workplace_type="on-site",
        application_url="https://jobs.example.com/tok",
        source_url="https://jobs.example.com/srctok",
    )

    result = evaluate_job_pair(job_london, job_tokyo)
    assert result.score <= 0.20


def test_template_description_false_positive_guard():
    """Boilerplate company templates must not cause distinct roles to be merged."""
    company_id = uuid.uuid4()
    common_template = (
        "We are an equal opportunity employer looking for talented professionals. "
        "Our mission is to empower teams with AI. Benefits include healthcare, 401k, "
        "flexible time off, and continuous learning opportunities."
    )

    job_engineer = make_test_job(
        company_id,
        "Cloud Security Engineer",
        description=common_template,
        application_url="https://jobs.example.com/eng",
        source_url="https://jobs.example.com/srceng",
    )
    job_accountant = make_test_job(
        company_id,
        "Senior Corporate Accountant",
        description=common_template,
        application_url="https://jobs.example.com/acc",
        source_url="https://jobs.example.com/srcacc",
    )

    result = evaluate_job_pair(job_engineer, job_accountant)
    assert result.score < 0.60
    assert result.match_type != MatchType.HIGH_CONFIDENCE.value


def test_high_confidence_duplicate_detection():
    """Similar titles, same company, compatible locations, and similar descriptions reach high confidence."""
    company_id = uuid.uuid4()
    job_a = make_test_job(
        company_id,
        "Senior Backend Engineer - Python",
        location="Bengaluru, Karnataka",
        workplace_type="remote",
        description="Build high-throughput distributed microservices with Python and FastAPI.",
        application_url=None,
        source_url=None,
    )
    job_b = make_test_job(
        company_id,
        "Senior Backend Engineer (Python)",
        location="Bangalore",
        workplace_type="remote",
        description="Build high-throughput distributed microservices with Python and FastAPI framework.",
        application_url=None,
        source_url=None,
    )

    result = evaluate_job_pair(job_a, job_b)
    assert result.score >= 0.90
    assert result.match_type == MatchType.HIGH_CONFIDENCE.value
