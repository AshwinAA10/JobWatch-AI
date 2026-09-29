"""Unit tests for title, location, workplace, employment, salary, and education dimensions."""

import uuid
from app.matching.models import CandidateMatchFeatures, DimensionStatus, JobMatchFeatures
from app.matching.rules import (
    evaluate_education,
    evaluate_employment_type,
    evaluate_location,
    evaluate_salary,
    evaluate_title,
    evaluate_workplace,
)


# --- Title Tests ---


def test_title_exact_and_alias_match():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        desired_titles=["software engineer"],
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Software Developer",  # "engineer" normalizes to "developer"
    )
    res = evaluate_title(candidate, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_title_substring_and_token_overlap():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        desired_titles=["Full Stack Developer"],
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Senior Full Stack Developer",
    )
    res = evaluate_title(candidate, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score >= 90.0


def test_title_no_overlap():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        desired_titles=["Data Scientist"],
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Frontend React Developer",
    )
    res = evaluate_title(candidate, job)
    assert res.status == DimensionStatus.MISMATCH
    assert res.score == 0.0


def test_title_missing_candidate_preference():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        desired_titles=[],
        current_title=None,
    )
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Software Engineer")
    res = evaluate_title(candidate, job)
    assert res.status == DimensionStatus.UNKNOWN
    assert res.score is None


# --- Location Tests ---


def test_location_remote_job():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        city="Coimbatore",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Developer",
        workplace_type="REMOTE",
        location="Anywhere",
    )
    res = evaluate_location(candidate, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_location_exact_city_match():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        city="Coimbatore",
        preferred_locations=["Coimbatore", "Chennai"],
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Developer",
        location="Coimbatore, India",
    )
    res = evaluate_location(candidate, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_location_relocation_allowed():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        city="Coimbatore",
        willing_to_relocate=True,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Developer",
        location="Bangalore",
    )
    res = evaluate_location(candidate, job)
    assert res.status == DimensionStatus.PARTIAL
    assert res.score == 75.0


def test_location_mismatch_without_relocation():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        city="Coimbatore",
        willing_to_relocate=False,
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Developer",
        location="Bangalore",
    )
    res = evaluate_location(candidate, job)
    assert res.status == DimensionStatus.MISMATCH
    assert res.score == 0.0


def test_location_missing():
    candidate = CandidateMatchFeatures(profile_id=uuid.uuid4())
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", location=None)
    res = evaluate_location(candidate, job)
    assert res.status == DimensionStatus.UNKNOWN
    assert res.score is None


# --- Workplace Tests ---


def test_workplace_matches():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        workplace_types=["REMOTE", "HYBRID"],
    )
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", workplace_type="REMOTE")
    res = evaluate_workplace(candidate, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_workplace_mismatch():
    candidate = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        workplace_types=["REMOTE"],
    )
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", workplace_type="ONSITE")
    res = evaluate_workplace(candidate, job)
    assert res.status == DimensionStatus.MISMATCH
    assert res.score == 0.0


def test_workplace_unknown():
    candidate = CandidateMatchFeatures(profile_id=uuid.uuid4(), workplace_types=[])
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", workplace_type=None)
    res = evaluate_workplace(candidate, job)
    assert res.status == DimensionStatus.UNKNOWN


# --- Employment Type Tests ---


def test_employment_type_matches_all_types():
    for et in ["FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "TEMPORARY"]:
        cand = CandidateMatchFeatures(profile_id=uuid.uuid4(), employment_types=[et])
        job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", employment_type=et)
        res = evaluate_employment_type(cand, job)
        assert res.status == DimensionStatus.MATCH
        assert res.score == 100.0


def test_employment_type_mismatch():
    cand = CandidateMatchFeatures(profile_id=uuid.uuid4(), employment_types=["FULL_TIME"])
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", employment_type="CONTRACT")
    res = evaluate_employment_type(cand, job)
    assert res.status == DimensionStatus.MISMATCH
    assert res.score == 0.0


# --- Salary Tests ---


def test_salary_meets_or_overlaps():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        minimum_salary=100000,
        maximum_salary=130000,
        salary_currency="USD",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        minimum_salary=110000,
        maximum_salary=140000,
        salary_currency="USD",
    )
    res = evaluate_salary(cand, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_salary_below_minimum_large_gap():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        minimum_salary=150000,
        salary_currency="USD",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        maximum_salary=100000,
        salary_currency="USD",
    )
    res = evaluate_salary(cand, job)
    assert res.status == DimensionStatus.MISMATCH
    assert res.score == 0.0


def test_salary_slight_gap():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        minimum_salary=100000,
        salary_currency="USD",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        maximum_salary=95000,  # 5% gap
        salary_currency="USD",
    )
    res = evaluate_salary(cand, job)
    assert res.status == DimensionStatus.PARTIAL
    assert res.score == 50.0


def test_salary_currency_mismatch():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        minimum_salary=100000,
        salary_currency="USD",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        minimum_salary=100000,
        salary_currency="EUR",
    )
    res = evaluate_salary(cand, job)
    assert res.status == DimensionStatus.UNKNOWN
    assert res.score is None


def test_salary_missing():
    cand = CandidateMatchFeatures(profile_id=uuid.uuid4())
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev")
    res = evaluate_salary(cand, job)
    assert res.status == DimensionStatus.UNKNOWN
    assert res.score is None


# --- Education Tests ---


def test_education_met():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        highest_education_level="Master's Degree",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        required_education_level="Bachelor's",
    )
    res = evaluate_education(cand, job)
    assert res.status == DimensionStatus.MATCH
    assert res.score == 100.0


def test_education_partial_one_tier_below():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        highest_education_level="Bachelor's",
    )
    job = JobMatchFeatures(
        job_id=uuid.uuid4(),
        title="Dev",
        required_education_level="Master's",
    )
    res = evaluate_education(cand, job)
    assert res.status == DimensionStatus.PARTIAL
    assert res.score == 50.0


def test_education_no_job_requirement():
    cand = CandidateMatchFeatures(
        profile_id=uuid.uuid4(),
        highest_education_level="Bachelor's",
    )
    job = JobMatchFeatures(job_id=uuid.uuid4(), title="Dev", required_education_level=None)
    res = evaluate_education(cand, job)
    assert res.status == DimensionStatus.NOT_APPLICABLE
    assert res.score is None
