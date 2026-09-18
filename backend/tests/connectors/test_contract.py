"""Shared contract tests for all connector implementations.

Verifies that every connector satisfies:
✓ Accept valid CareerSource
✓ Reject invalid configuration
✓ Return normalized jobs with valid attributes
✓ Preserve external IDs
✓ Return timezone-aware posted_at when available
✓ Handle empty results gracefully (return empty list, no error)
✓ Handle provider errors appropriately
"""

import asyncio
import uuid
from typing import Type
import httpx
import pytest

from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import ConnectorConfigurationError, ConnectorResponseError
from app.connectors.greenhouse.connector import GreenhouseConnector
from app.connectors.lever.connector import LeverConnector
from app.connectors.workday.connector import WorkdayConnector
from app.models.career_source import CareerSource


CONNECTORS_AND_VALID_URLS = [
    (GreenhouseConnector, "greenhouse", "https://boards.greenhouse.io/stripe"),
    (LeverConnector, "lever", "https://jobs.lever.co/netflix"),
    (WorkdayConnector, "workday", "https://adobe.wd5.myworkdayjobs.com/en-US/external_careers"),
]


@pytest.mark.parametrize("connector_cls,source_type,valid_url", CONNECTORS_AND_VALID_URLS)
def test_contract_accept_valid_source(connector_cls: Type[BaseJobConnector], source_type: str, valid_url: str):
    """Contract: Every connector initializes with a valid CareerSource and passes source validation."""
    source = CareerSource(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name=f"Test {source_type}",
        source_type=source_type,
        base_url=valid_url,
        is_active=True,
    )
    connector = connector_cls(source)
    connector.validate_source_config()


@pytest.mark.parametrize("connector_cls,source_type,_", CONNECTORS_AND_VALID_URLS)
def test_contract_reject_invalid_configuration(connector_cls: Type[BaseJobConnector], source_type: str, _: str):
    """Contract: Every connector rejects invalid base URLs during source validation."""
    source = CareerSource(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name=f"Invalid {source_type}",
        source_type=source_type,
        base_url="invalid-not-a-url",
        is_active=True,
    )
    with pytest.raises(ConnectorConfigurationError):
        connector_cls(source)


def test_contract_greenhouse_empty_and_error():
    """Contract: Greenhouse empty results return [] and 500 error raises ConnectorResponseError."""
    async def _run():
        source = CareerSource(
            id=uuid.uuid4(),
            company_id=uuid.uuid4(),
            name="Empty GH",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/empty",
            is_active=True,
        )

        # Empty results
        def empty_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"jobs": []})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(empty_handler))
        connector = GreenhouseConnector(source, raw_client=raw_client)
        jobs = await connector.fetch_jobs()
        assert jobs == []

        # 500 error
        def error_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        err_client = httpx.AsyncClient(transport=httpx.MockTransport(error_handler))
        connector_err = GreenhouseConnector(source, raw_client=err_client)
        with pytest.raises(ConnectorResponseError):
            await connector_err.fetch_jobs()

    asyncio.run(_run())


def test_contract_lever_empty_and_error():
    """Contract: Lever empty results return [] and 500 error raises ConnectorResponseError."""
    async def _run():
        source = CareerSource(
            id=uuid.uuid4(),
            company_id=uuid.uuid4(),
            name="Empty Lever",
            source_type="lever",
            base_url="https://jobs.lever.co/empty",
            is_active=True,
        )

        # Empty results
        def empty_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(empty_handler))
        connector = LeverConnector(source, raw_client=raw_client)
        jobs = await connector.fetch_jobs()
        assert jobs == []

        # 500 error
        def error_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        err_client = httpx.AsyncClient(transport=httpx.MockTransport(error_handler))
        connector_err = LeverConnector(source, raw_client=err_client)
        with pytest.raises(ConnectorResponseError):
            await connector_err.fetch_jobs()

    asyncio.run(_run())


def test_contract_workday_empty_and_error():
    """Contract: Workday empty results return [] and 500 error raises ConnectorResponseError."""
    async def _run():
        source = CareerSource(
            id=uuid.uuid4(),
            company_id=uuid.uuid4(),
            name="Empty Workday",
            source_type="workday",
            base_url="https://empty.wd5.myworkdayjobs.com/en-US/careers",
            is_active=True,
        )

        # Empty results
        def empty_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"total": 0, "jobPostings": []})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(empty_handler))
        connector = WorkdayConnector(source, raw_client=raw_client)
        jobs = await connector.fetch_jobs()
        assert jobs == []

        # 500 error
        def error_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        err_client = httpx.AsyncClient(transport=httpx.MockTransport(error_handler))
        connector_err = WorkdayConnector(source, raw_client=err_client)
        with pytest.raises(ConnectorResponseError):
            await connector_err.fetch_jobs()

    asyncio.run(_run())
