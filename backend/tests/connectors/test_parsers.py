"""Unit tests for Greenhouse, Lever, and Workday response parsers."""

import json
from pathlib import Path
import pytest

from app.connectors.greenhouse.parser import GreenhouseParser
from app.connectors.lever.parser import LeverParser
from app.connectors.workday.parser import WorkdayParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_greenhouse_parser_with_fixture():
    """Verify GreenhouseParser correctly normalizes fixture data."""
    fixture_path = FIXTURES_DIR / "greenhouse" / "jobs_response.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    parser = GreenhouseParser()
    normalized_jobs = parser.parse_jobs_response(data)

    assert len(normalized_jobs) == 3

    # Job 1
    job1 = normalized_jobs[0]
    assert job1.external_id == "4829101"
    assert job1.title == "Senior Backend Engineer - Python"
    assert job1.location == "San Francisco, CA (Remote)"
    assert job1.workplace_type == "remote"
    assert job1.employment_type == "full_time"
    assert job1.application_url == "https://boards.greenhouse.io/acme/jobs/4829101"
    assert job1.source_url == "https://boards.greenhouse.io/acme/jobs/4829101"
    assert job1.posted_at is not None
    assert job1.posted_at.tzinfo is not None  # timezone-aware UTC

    # Job 2
    job2 = normalized_jobs[1]
    assert job2.external_id == "4829102"
    assert job2.title == "Data Engineering Intern"
    assert job2.location == "New York, NY"
    assert job2.employment_type == "internship"


def test_greenhouse_parser_handles_malformed_records():
    """Verify single malformed record is skipped without crashing valid ones."""
    data = {
        "jobs": [
            {"id": "valid-1", "title": "Valid Job 1", "absolute_url": "https://example.com/1"},
            {"id": None, "title": "Missing ID"},  # Invalid
            {"id": "valid-2", "title": "Valid Job 2", "absolute_url": "https://example.com/2"},
        ]
    }
    parser = GreenhouseParser()
    jobs = parser.parse_jobs_response(data)
    assert len(jobs) == 2
    assert [j.external_id for j in jobs] == ["valid-1", "valid-2"]


def test_lever_parser_with_fixture():
    """Verify LeverParser correctly normalizes fixture data."""
    fixture_path = FIXTURES_DIR / "lever" / "postings_response.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    parser = LeverParser()
    normalized_jobs = parser.parse_postings_response(data)

    assert len(normalized_jobs) == 3

    # Job 1
    job1 = normalized_jobs[0]
    assert job1.external_id == "lev-101"
    assert job1.title == "Senior Backend Engineer"
    assert job1.location == "San Francisco, CA"
    assert job1.workplace_type == "remote"
    assert job1.employment_type == "full_time"
    assert job1.application_url == "https://jobs.lever.co/acme/lev-101/apply"
    assert job1.source_url == "https://jobs.lever.co/acme/lev-101"
    assert job1.posted_at is not None
    assert job1.posted_at.tzinfo is not None

    # Job 2
    job2 = normalized_jobs[1]
    assert job2.external_id == "lev-102"
    assert job2.title == "Product Designer"
    assert job2.workplace_type == "hybrid"
    assert job2.employment_type == "part_time"

    # Job 3
    job3 = normalized_jobs[2]
    assert job3.external_id == "lev-103"
    assert job3.workplace_type == "onsite"
    assert job3.employment_type == "contract"
    assert job3.posted_at is None  # no timestamp provided


def test_lever_parser_handles_malformed_records():
    """Verify LeverParser skips invalid records gracefully."""
    data = [
        {"id": "valid-1", "text": "Engineer", "hostedUrl": "https://jobs.lever.co/test/1"},
        {"not_an_id": "bad"},
        {"id": "valid-2", "text": "Designer", "hostedUrl": "https://jobs.lever.co/test/2"},
    ]
    parser = LeverParser()
    jobs = parser.parse_postings_response(data)
    assert len(jobs) == 2
    assert [j.external_id for j in jobs] == ["valid-1", "valid-2"]


def test_workday_parser_with_fixture():
    """Verify WorkdayParser correctly normalizes fixture data."""
    fixture_path = FIXTURES_DIR / "workday" / "search_response.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    parser = WorkdayParser(
        host="acme.myworkdayjobs.com",
        tenant="acme",
        site="careers",
    )
    normalized_jobs = parser.parse_search_response(data)

    assert len(normalized_jobs) == 3

    # Job 1
    job1 = normalized_jobs[0]
    assert job1.external_id == "JR-100234"
    assert job1.title == "Staff Platform Engineer"
    assert job1.location == "San Francisco, CA"
    assert job1.employment_type == "full_time"
    assert "https://acme.myworkdayjobs.com/en-US/careers/job/San-Francisco/Staff-Platform-Engineer_JR-100234" in job1.application_url

    # Job 2
    job2 = normalized_jobs[1]
    assert job2.external_id == "R-98765"
    assert job2.title == "Data Scientist"
    assert job2.location == "New York, NY"
    assert job2.employment_type == "full_time"

    # Job 3
    job3 = normalized_jobs[2]
    assert job3.external_id == "INT-44321"
    assert job3.title == "Summer Intern - Engineering"
    assert job3.employment_type == "part_time"
    assert job3.workplace_type == "remote"


def test_workday_parser_handles_malformed_records():
    """Verify WorkdayParser skips malformed postings gracefully."""
    data = {
        "jobPostings": [
            {"title": "Valid Job", "externalPath": "/job/123_R-1"},
            {"no_title": True},
            {"title": "Valid Job 2", "externalPath": "/job/456_R-2"},
        ]
    }
    parser = WorkdayParser(host="example.com", tenant="acme", site="jobs")
    jobs = parser.parse_search_response(data)
    assert len(jobs) == 2
    assert [j.external_id for j in jobs] == ["R-1", "R-2"]
