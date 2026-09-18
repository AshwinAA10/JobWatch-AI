"""Resilient HTTP client foundation for external career portal connectors."""

import asyncio
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import httpx

from app.connectors.exceptions import (
    ConnectorConfigurationError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
)

logger = logging.getLogger("jobwatch.connectors.http")

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=25.0, write=10.0, pool=10.0)
DEFAULT_USER_AGENT = "JobWatchAI-Connector/0.1.0 (+https://github.com/AshwinAA10/JobWatch-AI)"
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


def validate_url(url: str, source_type: Optional[str] = None) -> None:
    """Validate that a URL uses an allowed HTTP/HTTPS scheme and has a valid network location."""
    if not url or not isinstance(url, str):
        raise ConnectorConfigurationError(
            "Base URL cannot be empty or non-string",
            source_type=source_type,
        )

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ConnectorConfigurationError(
            f"Invalid URL scheme '{parsed.scheme}'. Only http and https are permitted.",
            source_type=source_type,
        )
    if not parsed.netloc:
        raise ConnectorConfigurationError(
            f"Invalid URL '{url}': missing host/network location.",
            source_type=source_type,
        )


class ConnectorHttpClient:
    """Asynchronous HTTP client with bounded retries, rate-limit backoff, and error mapping."""

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        source_type: Optional[str] = None,
        max_retries: int = 3,
        base_backoff: float = 0.5,
        max_backoff: float = 5.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.source_type = source_type
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self._custom_headers = headers or {}
        self._external_client = client
        self._internal_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            headers = {"User-Agent": DEFAULT_USER_AGENT, **self._custom_headers}
            self._internal_client = httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                headers=headers,
                follow_redirects=True,
            )
        return self._internal_client

    async def close(self) -> None:
        """Close internally managed AsyncClient instance."""
        if self._internal_client is not None and not self._internal_client.is_closed:
            await self._internal_client.aclose()
            self._internal_client = None

    async def __aenter__(self) -> "ConnectorHttpClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _parse_retry_after(self, response: httpx.Response) -> Optional[float]:
        header_val = response.headers.get("Retry-After")
        if not header_val:
            return None
        try:
            return min(float(header_val), 10.0)  # Bound retry-after wait to 10s max
        except ValueError:
            return None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute an asynchronous HTTP request with bounded retries on transient errors."""
        validate_url(url, source_type=self.source_type)
        client = self._get_client()

        attempt = 0
        while True:
            attempt += 1
            try:
                logger.debug(
                    "[%s] %s %s (attempt %d/%d)",
                    self.source_type or "HTTP",
                    method.upper(),
                    url,
                    attempt,
                    self.max_retries + 1,
                )
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )

                # If status is successful (2xx), return response immediately
                if response.is_success:
                    return response

                status = response.status_code

                # Check for transient retryable errors
                if status in RETRYABLE_STATUS_CODES and attempt <= self.max_retries:
                    retry_delay = self._parse_retry_after(response) or min(
                        self.base_backoff * (2 ** (attempt - 1)),
                        self.max_backoff,
                    )
                    logger.warning(
                        "[%s] Received HTTP %d from %s. Retrying in %.2fs (attempt %d)",
                        self.source_type or "HTTP",
                        status,
                        url,
                        retry_delay,
                        attempt,
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                # Map non-transient or exhausted status codes to typed exceptions
                self._handle_error_response(response)

            except httpx.TimeoutException as exc:
                if attempt <= self.max_retries:
                    backoff = min(self.base_backoff * (2 ** (attempt - 1)), self.max_backoff)
                    logger.warning(
                        "[%s] Timeout contacting %s. Retrying in %.2fs",
                        self.source_type or "HTTP",
                        url,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise ConnectorRequestError(
                    f"Request timed out after {attempt} attempts: {url}",
                    source_type=self.source_type,
                ) from exc

            except httpx.NetworkError as exc:
                if attempt <= self.max_retries:
                    backoff = min(self.base_backoff * (2 ** (attempt - 1)), self.max_backoff)
                    logger.warning(
                        "[%s] Network error contacting %s. Retrying in %.2fs",
                        self.source_type or "HTTP",
                        url,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise ConnectorRequestError(
                    f"Network transport error connecting to {url}: {exc}",
                    source_type=self.source_type,
                ) from exc

    def _handle_error_response(self, response: httpx.Response) -> None:
        status = response.status_code
        if status == 429:
            retry_after = self._parse_retry_after(response)
            raise ConnectorRateLimitError(
                f"Rate limit exceeded (HTTP 429): {response.url}",
                source_type=self.source_type,
                retry_after=retry_after,
            )
        if status in {401, 403}:
            raise ConnectorConfigurationError(
                f"Access denied by provider (HTTP {status}): {response.url}",
                source_type=self.source_type,
            )
        if status == 404:
            raise ConnectorConfigurationError(
                f"Target career board or endpoint not found (HTTP 404): {response.url}",
                source_type=self.source_type,
            )
        if 400 <= status < 500:
            raise ConnectorResponseError(
                f"Client error from provider (HTTP {status}): {response.url}",
                status_code=status,
                source_type=self.source_type,
            )
        if status >= 500:
            raise ConnectorResponseError(
                f"Provider service failure (HTTP {status}): {response.url}",
                status_code=status,
                source_type=self.source_type,
            )

        raise ConnectorResponseError(
            f"Unexpected HTTP response {status} from {response.url}",
            status_code=status,
            source_type=self.source_type,
        )

    async def get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Fetch a GET endpoint and parse JSON response."""
        response = await self.request("GET", url, params=params, headers=headers)
        try:
            return response.json()
        except Exception as exc:
            raise ConnectorResponseError(
                f"Failed to decode JSON response from {url}",
                status_code=response.status_code,
                source_type=self.source_type,
            ) from exc

    async def post_json(
        self,
        url: str,
        *,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute a POST request with JSON body and return parsed JSON response."""
        response = await self.request("POST", url, params=params, json=json, headers=headers)
        try:
            return response.json()
        except Exception as exc:
            raise ConnectorResponseError(
                f"Failed to decode JSON response from {url}",
                status_code=response.status_code,
                source_type=self.source_type,
            ) from exc
