"""Tests for ConnectorHttpClient resilience, retries, and error handling using httpx.MockTransport."""

import asyncio
import httpx
import pytest

from app.connectors.exceptions import (
    ConnectorConfigurationError,
    ConnectorRateLimitError,
    ConnectorResponseError,
)
from app.connectors.http import ConnectorHttpClient, validate_url


def test_validate_url():
    """Verify URL validation security rules."""
    # Valid URLs
    validate_url("https://boards.greenhouse.io/v1/boards/stripe/jobs")
    validate_url("http://localhost:8000/api")

    # Invalid schemes and formats
    with pytest.raises(ConnectorConfigurationError, match="Invalid URL scheme"):
        validate_url("file:///etc/passwd")

    with pytest.raises(ConnectorConfigurationError, match="Invalid URL scheme"):
        validate_url("ftp://example.com/jobs")

    with pytest.raises(ConnectorConfigurationError, match="Invalid URL scheme"):
        validate_url("not-a-valid-url")

    with pytest.raises(ConnectorConfigurationError, match="missing host"):
        validate_url("http://")

    with pytest.raises(ConnectorConfigurationError, match="cannot be empty"):
        validate_url("")


def test_get_json_success():
    """Verify successful GET JSON request."""
    async def _run():
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert str(request.url) == "https://api.example.com/jobs"
            return httpx.Response(200, json={"jobs": [{"id": 1, "title": "Dev"}]})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client) as client:
            data = await client.get_json("https://api.example.com/jobs")
            assert data == {"jobs": [{"id": 1, "title": "Dev"}]}

    asyncio.run(_run())


def test_non_retryable_4xx_errors():
    """Verify 4xx errors are not retried and raise appropriate typed exceptions."""
    async def _run():
        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if "/400" in path:
                return httpx.Response(400)
            if "/401" in path:
                return httpx.Response(401)
            if "/404" in path:
                return httpx.Response(404)
            return httpx.Response(200)

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client, max_retries=3) as client:
            # 400 Bad Request -> ConnectorResponseError (client error)
            with pytest.raises(ConnectorResponseError) as exc_info:
                await client.request("GET", "https://api.example.com/400")
            assert exc_info.value.status_code == 400

            # 401 Unauthorized -> ConnectorConfigurationError
            with pytest.raises(ConnectorConfigurationError):
                await client.request("GET", "https://api.example.com/401")

            # 404 Not Found -> ConnectorConfigurationError
            with pytest.raises(ConnectorConfigurationError):
                await client.request("GET", "https://api.example.com/404")

    asyncio.run(_run())


def test_retry_on_5xx_transient_failure():
    """Verify transient 5xx errors are retried up to max_retries."""
    async def _run():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(503)
            return httpx.Response(200, json={"status": "recovered"})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client, max_retries=3, base_backoff=0.001) as client:
            data = await client.get_json("https://api.example.com/flaky")
            assert data == {"status": "recovered"}
            assert call_count == 3

    asyncio.run(_run())


def test_exhausted_retries_raises_response_error():
    """Verify exhausting retries raises ConnectorResponseError."""
    async def _run():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(503)

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client, max_retries=2, base_backoff=0.001) as client:
            with pytest.raises(ConnectorResponseError) as exc_info:
                await client.request("GET", "https://api.example.com/always-503")
            assert exc_info.value.status_code == 503
            assert call_count == 3  # initial + 2 retries

    asyncio.run(_run())


def test_rate_limit_429_with_retry_after():
    """Verify 429 rate limit is retried with Retry-After header."""
    async def _run():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(429, headers={"Retry-After": "0.001"})
            return httpx.Response(200, json={"ok": True})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client, max_retries=2, base_backoff=0.001) as client:
            data = await client.get_json("https://api.example.com/rate-limited")
            assert data == {"ok": True}
            assert call_count == 2

    asyncio.run(_run())


def test_rate_limit_429_exhausted():
    """Verify persistent 429 raises ConnectorRateLimitError."""
    async def _run():
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(429, headers={"Retry-After": "0.001"})

        raw_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        async with ConnectorHttpClient(client=raw_client, max_retries=1, base_backoff=0.001) as client:
            with pytest.raises(ConnectorRateLimitError) as exc_info:
                await client.request("GET", "https://api.example.com/rate-limited-forever")
            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after == 0.001

    asyncio.run(_run())
