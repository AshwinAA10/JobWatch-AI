"""Integration tests for JobIngestionService and database persistence."""

import asyncio
import uuid
import httpx
import pytest
from sqlalchemy.orm import Session

from app.connectors.exceptions import ConnectorConfigurationError
from app.models.company import Company
from app.models.career_source import CareerSource
from app.models.job import Job
from app.repositories.job import JobRepository
from app.services.ingestion import JobIngestionService


def create_test_company_and_source(
    db: Session,
    source_type: str = "greenhouse",
    base_url: str = "https://boards.greenhouse.io/acme",
    is_active: bool = True,
) -> CareerSource:
    """Helper to create a Company and CareerSource in the test database."""
    company = Company(
        id=uuid.uuid4(),
        name="Acme Corporation",
        slug=f"acme-{uuid.uuid4().hex[:8]}",
        website_url="https://acme.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name=f"Acme {source_type.capitalize()}",
        source_type=source_type,
        base_url=base_url,
        is_active=is_active,
    )
    db.add(source)
    db.commit()
    return source


def test_ingestion_service_greenhouse_success(db_session: Session):
    """Verify JobIngestionService fetches, normalizes, and persists jobs to DB."""
    async def _run():
        source = create_test_company_and_source(db_session, "greenhouse", "https://boards.greenhouse.io/acme")

        # Mock Greenhouse API using MockTransport
        def handler(request: httpx.Request) -> httpx.Response:
            assert "boards-api.greenhouse.io" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": 501,
                            "title": "Software Engineer",
                            "absolute_url": "https://boards.greenhouse.io/acme/jobs/501",
                            "location": {"name": "Remote"},
                        },
                        {
                            "id": 502,
                            "title": "Product Manager",
                            "absolute_url": "https://boards.greenhouse.io/acme/jobs/502",
                            "location": {"name": "New York, NY"},
                        },
                    ]
                },
            )

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = JobIngestionService(db_session, raw_client=raw_client)
        result = await service.ingest_source(source.id)

        assert result.source_id == source.id
        assert result.jobs_fetched == 2
        assert result.jobs_persisted == 2
        assert result.jobs_updated == 0
        assert result.jobs_skipped == 0
        assert result.duration_seconds > 0

        # Query DB directly to verify records
        job_repo = JobRepository(db_session)
        jobs = job_repo.list_by_company(source.company_id)
        assert len(jobs) == 2
        titles = {j.title for j in jobs}
        assert "Software Engineer" in titles
        assert "Product Manager" in titles

        # Ingest again: should update/refresh, not create duplicates
        result_repeat = await service.ingest_source(source.id)
        assert result_repeat.jobs_fetched == 2
        assert result_repeat.jobs_persisted == 0
        assert result_repeat.jobs_updated == 2

        # Total rows in DB is still 2
        jobs_after = job_repo.list_by_company(source.company_id)
        assert len(jobs_after) == 2

    asyncio.run(_run())


def test_ingestion_service_inactive_source(db_session: Session):
    """Verify inactive CareerSource is rejected."""
    async def _run():
        source = create_test_company_and_source(
            db_session,
            "greenhouse",
            "https://boards.greenhouse.io/inactive",
            is_active=False,
        )

        service = JobIngestionService(db_session)
        with pytest.raises(ConnectorConfigurationError, match="is inactive"):
            await service.ingest_source(source.id)

    asyncio.run(_run())


def test_ingestion_service_not_found(db_session: Session):
    """Verify non-existent CareerSource raises ConnectorConfigurationError."""
    async def _run():
        service = JobIngestionService(db_session)
        with pytest.raises(ConnectorConfigurationError, match="does not exist"):
            await service.ingest_source(uuid.uuid4())

    asyncio.run(_run())
