"""Unit and mocked-HTTP tests for Greenhouse, Lever, and Workday connectors."""

import asyncio
import uuid
import httpx
import pytest

from app.connectors.exceptions import (
    ConnectorConfigurationError,
    UnsupportedConnectorError,
)
from app.connectors.factory import ConnectorFactory
from app.connectors.greenhouse.connector import GreenhouseConnector
from app.connectors.lever.connector import LeverConnector
from app.connectors.workday.connector import WorkdayConnector
from app.models.career_source import CareerSource


def make_dummy_source(source_type: str, base_url: str) -> CareerSource:
    """Helper to create dummy in-memory CareerSource model."""
    return CareerSource(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name=f"Test {source_type}",
        source_type=source_type,
        base_url=base_url,
        is_active=True,
    )


def test_factory_and_registry():
    """Verify ConnectorFactory produces appropriate connector instances."""
    gh_source = make_dummy_source("greenhouse", "https://boards.greenhouse.io/stripe")
    lev_source = make_dummy_source("lever", "https://jobs.lever.co/netflix")
    wd_source = make_dummy_source("workday", "https://adobe.wd5.myworkdayjobs.com/en-US/external_careers")

    assert isinstance(ConnectorFactory.create(gh_source), GreenhouseConnector)
    assert isinstance(ConnectorFactory.create(lev_source), LeverConnector)
    assert isinstance(ConnectorFactory.create(wd_source), WorkdayConnector)

    # Unsupported provider
    bad_source = make_dummy_source("unknown_ats", "https://example.com")
    with pytest.raises(UnsupportedConnectorError, match="Unsupported career source type"):
        ConnectorFactory.create(bad_source)


def test_greenhouse_connector_fetch_jobs():
    """Verify GreenhouseConnector fetches and normalizes jobs."""
    async def _run():
        source = make_dummy_source("greenhouse", "https://boards.greenhouse.io/acme")

        def handler(request: httpx.Request) -> httpx.Response:
            assert "boards-api.greenhouse.io/v1/boards/acme/jobs" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": 1001,
                            "title": "Backend Engineer",
                            "absolute_url": "https://boards.greenhouse.io/acme/jobs/1001",
                            "location": {"name": "Remote"},
                        }
                    ]
                },
            )

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        connector = GreenhouseConnector(source, raw_client=raw_client)

        jobs = await connector.fetch_jobs()
        assert len(jobs) == 1
        assert jobs[0].external_id == "1001"
        assert jobs[0].title == "Backend Engineer"
        assert jobs[0].workplace_type == "remote"

    asyncio.run(_run())


def test_greenhouse_connector_invalid_config():
    """Verify GreenhouseConnector rejects invalid base URL."""
    source = make_dummy_source("greenhouse", "not-a-url")
    with pytest.raises(ConnectorConfigurationError):
        GreenhouseConnector(source)


def test_lever_connector_pagination():
    """Verify LeverConnector handles pagination loop properly."""
    async def _run():
        source = make_dummy_source("lever", "https://jobs.lever.co/acme")

        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            query = request.url.query.decode("utf-8")
            if "skip=0" in query:
                return httpx.Response(
                    200,
                    json=[
                        {"id": "p1-1", "text": "Engineer 1", "hostedUrl": "https://jobs.lever.co/acme/p1-1"},
                        {"id": "p1-2", "text": "Engineer 2", "hostedUrl": "https://jobs.lever.co/acme/p1-2"},
                    ],
                )
            return httpx.Response(200, json=[])

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        connector = LeverConnector(source, raw_client=raw_client)

        jobs = await connector.fetch_jobs()
        assert len(jobs) == 2
        assert [j.external_id for j in jobs] == ["p1-1", "p1-2"]

    asyncio.run(_run())


def test_workday_connector_pagination():
    """Verify WorkdayConnector handles CXS search POST and pagination."""
    async def _run():
        source = make_dummy_source("workday", "https://acme.wd5.myworkdayjobs.com/en-US/careers")

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/wday/cxs/acme/careers/jobs" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "total": 2,
                    "limit": 20,
                    "offset": 0,
                    "jobPostings": [
                        {"title": "Role A", "externalPath": "/job/Role-A_JR-1"},
                        {"title": "Role B", "externalPath": "/job/Role-B_JR-2"},
                    ],
                },
            )

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        connector = WorkdayConnector(source, raw_client=raw_client)

        jobs = await connector.fetch_jobs()
        assert len(jobs) == 2
        assert [j.external_id for j in jobs] == ["JR-1", "JR-2"]

    asyncio.run(_run())
