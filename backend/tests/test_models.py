"""Tests for SQLAlchemy ORM models, constraints, and relationships."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job


def test_company_creation(db_session: Session):
    """Verify Company creation with UUID primary key and UTC timestamps."""
    company = Company(
        name="Acme Corporation",
        slug="acme-corp",
        website_url="https://acme.example.com",
        description="Pioneering industrial solutions",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    assert isinstance(company.id, uuid.UUID)
    assert company.name == "Acme Corporation"
    assert company.slug == "acme-corp"
    assert company.created_at is not None
    assert company.updated_at is not None
    assert company.is_active is True


def test_company_slug_unique_constraint(db_session: Session):
    """Verify that duplicate company slugs raise IntegrityError."""
    c1 = Company(name="Company One", slug="duplicate-slug")
    c2 = Company(name="Company Two", slug="duplicate-slug")
    db_session.add(c1)
    db_session.flush()

    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_career_source_relationships(db_session: Session):
    """Verify CareerSource creation and bi-directional Company relationship."""
    company = Company(name="Tech Innovations", slug="tech-innovations")
    db_session.add(company)
    db_session.flush()

    source = CareerSource(
        company_id=company.id,
        name="Greenhouse Board",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/techinnovations",
    )
    db_session.add(source)
    db_session.flush()

    assert source.company.name == "Tech Innovations"
    assert len(company.career_sources) == 1
    assert company.career_sources[0].name == "Greenhouse Board"


def test_job_composite_unique_constraint(db_session: Session):
    """Verify composite uniqueness of (career_source_id, external_id) on Job."""
    company = Company(name="Global Systems", slug="global-systems")
    db_session.add(company)
    db_session.flush()

    source = CareerSource(
        company_id=company.id,
        name="Lever Jobs",
        source_type="lever",
        base_url="https://jobs.lever.co/globalsystems",
    )
    db_session.add(source)
    db_session.flush()

    job1 = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="JOB-101",
        title="Senior Software Engineer",
    )
    db_session.add(job1)
    db_session.flush()

    job2 = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="JOB-101",  # Duplicate within the same career source
        title="Another Title with Same ID",
    )
    db_session.add(job2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_cascade_delete_company_deletes_sources_and_jobs(db_session: Session):
    """Verify cascading deletion of company deletes associated sources and jobs."""
    company = Company(name="Cascade Corp", slug="cascade-corp")
    db_session.add(company)
    db_session.flush()

    source = CareerSource(
        company_id=company.id,
        name="Main Board",
        source_type="workday",
        base_url="https://workday.example.com",
    )
    db_session.add(source)
    db_session.flush()

    job = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="JOB-CASCADE",
        title="Site Reliability Engineer",
    )
    db_session.add(job)
    db_session.flush()

    # Delete company
    db_session.delete(company)
    db_session.flush()

    assert db_session.get(Company, company.id) is None
    assert db_session.get(CareerSource, source.id) is None
    assert db_session.get(Job, job.id) is None
