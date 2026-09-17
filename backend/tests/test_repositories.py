"""Tests for Repository pattern data access layer."""

from sqlalchemy.orm import Session

from app.repositories.career_source import CareerSourceRepository
from app.repositories.company import CompanyRepository
from app.repositories.job import JobRepository
from app.schemas.career_source import CareerSourceCreate
from app.schemas.company import CompanyCreate
from app.schemas.job import JobCreate


def test_company_repository_crud(db_session: Session):
    """Verify CompanyRepository CRUD operations."""
    repo = CompanyRepository(db_session)

    # 1. Create
    company_in = CompanyCreate(
        name="Alpha Labs",
        slug="alpha-labs",
        website_url="https://alpha.example.com",
        is_active=True,
    )
    company = repo.create(company_in)
    assert company.id is not None
    assert company.slug == "alpha-labs"

    # 2. Get by ID
    by_id = repo.get_by_id(company.id)
    assert by_id is not None
    assert by_id.name == "Alpha Labs"

    # 3. Get by slug
    by_slug = repo.get_by_slug("alpha-labs")
    assert by_slug is not None
    assert by_slug.id == company.id

    # 4. List active
    inactive_in = CompanyCreate(name="Beta Corp", slug="beta-corp", is_active=False)
    repo.create(inactive_in)

    active_companies = repo.list_active()
    assert any(c.slug == "alpha-labs" for c in active_companies)
    assert not any(c.slug == "beta-corp" for c in active_companies)

    # 5. List all
    all_companies = repo.list_all()
    assert len(all_companies) >= 2


def test_career_source_repository(db_session: Session):
    """Verify CareerSourceRepository operations."""
    company_repo = CompanyRepository(db_session)
    source_repo = CareerSourceRepository(db_session)

    company = company_repo.create(CompanyCreate(name="Source Corp", slug="source-corp"))

    source_in = CareerSourceCreate(
        company_id=company.id,
        name="Greenhouse Portal",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/sourcecorp",
        is_active=True,
    )
    source = source_repo.create(source_in)
    assert source.id is not None
    assert source.company_id == company.id

    # Get by ID
    fetched = source_repo.get_by_id(source.id)
    assert fetched is not None
    assert fetched.name == "Greenhouse Portal"

    # List by company
    sources = source_repo.list_by_company(company.id)
    assert len(sources) == 1
    assert sources[0].id == source.id


def test_job_repository(db_session: Session):
    """Verify JobRepository operations."""
    company_repo = CompanyRepository(db_session)
    source_repo = CareerSourceRepository(db_session)
    job_repo = JobRepository(db_session)

    company = company_repo.create(CompanyCreate(name="JobHub Inc", slug="jobhub"))
    source = source_repo.create(
        CareerSourceCreate(
            company_id=company.id,
            name="Main ATS",
            source_type="lever",
            base_url="https://jobs.lever.co/jobhub",
        )
    )

    # Create job
    job_in = JobCreate(
        company_id=company.id,
        career_source_id=source.id,
        external_id="EXT-9001",
        title="Full Stack Engineer",
        description="Build scalable web applications",
        location="Remote",
        employment_type="full-time",
        is_active=True,
    )
    job = job_repo.create(job_in)
    assert job.id is not None
    assert job.title == "Full Stack Engineer"

    # Get by ID
    fetched = job_repo.get_by_id(job.id)
    assert fetched is not None
    assert fetched.external_id == "EXT-9001"

    # Get by external ID within source
    by_ext = job_repo.get_by_external_id(source.id, "EXT-9001")
    assert by_ext is not None
    assert by_ext.id == job.id

    # List active jobs
    active_jobs = job_repo.list_active()
    assert any(j.id == job.id for j in active_jobs)

    # List by company
    company_jobs = job_repo.list_by_company(company.id)
    assert len(company_jobs) == 1
    assert company_jobs[0].id == job.id
