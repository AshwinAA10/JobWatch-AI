"""Unit tests for deterministic normalization helpers."""

from app.deduplication.normalizers import (
    clean_text,
    extract_seniority,
    normalize_location,
    normalize_title,
    normalize_url,
)


def test_clean_text():
    """Verify HTML stripping, entity decoding, and whitespace collapsing."""
    raw_html = "<p>Join our <strong>Engineering</strong> team! &amp; build scalable systems.&nbsp;&nbsp;</p>"
    cleaned = clean_text(raw_html)
    assert cleaned == "join our engineering team! & build scalable systems."

    assert clean_text(None) == ""
    assert clean_text("   ") == ""


def test_normalize_title():
    """Verify title normalization preserves meaningful seniority and specialization tokens."""
    assert normalize_title("Senior Software Engineer - Backend") == "senior software engineer backend"
    assert normalize_title("Software Engineer II (Remote)") == "software engineer ii remote"
    assert normalize_title("Staff Engineer / Tech Lead [Platform]") == "staff engineer tech lead platform"
    assert normalize_title("Product Designer & Researcher") == "product designer researcher"
    assert normalize_title("") == ""


def test_extract_seniority():
    """Verify accurate extraction of canonical seniority tiers."""
    assert extract_seniority("Software Engineering Intern") == "intern"
    assert extract_seniority("Summer 2026 Co-op - Developer") == "intern"
    assert extract_seniority("Junior Python Developer") == "junior"
    assert extract_seniority("Associate Software Engineer") == "junior"
    assert extract_seniority("Software Engineer I") == "junior"
    assert extract_seniority("Software Engineer II") == "mid"
    assert extract_seniority("Senior Frontend Engineer") == "senior"
    assert extract_seniority("Sr. Backend Developer") == "senior"
    assert extract_seniority("Software Engineer III") == "senior"
    assert extract_seniority("Staff Site Reliability Engineer") == "staff"
    assert extract_seniority("Tech Lead - Infrastructure") == "lead"
    assert extract_seniority("Principal Systems Architect") == "principal"
    assert extract_seniority("Engineering Manager, Core Services") == "manager"
    assert extract_seniority("Director of Engineering") == "director"
    assert extract_seniority("VP, Data Science") == "director"
    assert extract_seniority("Software Engineer") is None


def test_normalize_location():
    """Verify location normalization and city alias resolution."""
    assert normalize_location("Bangalore, India") == "bengaluru, india"
    assert normalize_location("Gurgaon, HR") == "gurugram, hr"
    assert normalize_location("New York City, NY") == "new york, ny"
    assert normalize_location("SF Bay Area, CA") == "san francisco, ca"
    assert normalize_location("Remote - US") == "remote us"
    assert normalize_location(None) is None
    assert normalize_location("") is None


def test_normalize_url():
    """Verify URL canonicalization removes marketing trackers while strictly preserving job requisition IDs."""
    dirty_url = (
        "https://boards.greenhouse.io/stripe/jobs/1234567/"
        "?gh_src=linkedin&utm_source=jobboard&utm_medium=cpc&utm_campaign=eng#application"
    )
    normalized = normalize_url(dirty_url)
    assert normalized == "https://boards.greenhouse.io/stripe/jobs/1234567"

    # Preserves job query parameters
    param_job_url = (
        "https://jobs.example.com/apply?id=98765&ref=homepage&utm_source=twitter"
    )
    norm_param_url = normalize_url(param_job_url)
    assert norm_param_url == "https://jobs.example.com/apply?id=98765"

    assert normalize_url(None) is None
    assert normalize_url("") is None
