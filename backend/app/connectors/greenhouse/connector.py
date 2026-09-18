"""Greenhouse Job Board API connector."""

import logging
import re
from typing import List
from urllib.parse import urlparse

from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import ConnectorConfigurationError, ConnectorParseError
from app.connectors.greenhouse.parser import GreenhouseParser
from app.connectors.greenhouse.schemas import GreenhouseJobsResponse
from app.connectors.models import NormalizedJob

logger = logging.getLogger("jobwatch.connectors.greenhouse")

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


def extract_board_token(base_url: str) -> str:
    """Extract the Greenhouse board token identifier from a URL or raw slug.
    
    Examples:
        'https://boards.greenhouse.io/stripe' -> 'stripe'
        'https://boards-api.greenhouse.io/v1/boards/stripe/jobs' -> 'stripe'
        'https://job-boards.greenhouse.io/stripe' -> 'stripe'
        'stripe' -> 'stripe'
    """
    if not base_url or not isinstance(base_url, str):
        raise ConnectorConfigurationError(
            "Greenhouse base_url is required",
            source_type="greenhouse",
        )

    clean_url = base_url.strip().rstrip("/")
    if "/" not in clean_url:
        token = clean_url
    else:
        parsed = urlparse(clean_url)
        path = parsed.path.strip("/")
        # Path might be: 'v1/boards/{token}/jobs' or '{token}'
        match = re.search(r"(?:boards/)?([^/]+)(?:/jobs)?$", path)
        if match and match.group(1):
            token = match.group(1)
        else:
            token = path.split("/")[-1]

    if not token or token in {"jobs", "v1", "boards"}:
        raise ConnectorConfigurationError(
            f"Could not extract valid Greenhouse board token from '{base_url}'",
            source_type="greenhouse",
        )
    return token


class GreenhouseConnector(BaseJobConnector):
    """Connector for querying Greenhouse Job Board API."""

    source_type: str = "greenhouse"

    def validate_source_config(self) -> None:
        """Validate that the Greenhouse board token can be extracted."""
        self.board_token = extract_board_token(self.source.base_url)

    async def fetch_jobs(self) -> List[NormalizedJob]:
        """Fetch and normalize all active jobs from the Greenhouse board."""
        endpoint = f"{GREENHOUSE_API_BASE}/{self.board_token}/jobs"
        params = {"content": "true"}

        logger.info(
            "Fetching Greenhouse jobs for board '%s' (source_id=%s)",
            self.board_token,
            self.source.id,
        )

        data = await self.http.get_json(endpoint, params=params)

        try:
            payload = GreenhouseJobsResponse.model_validate(data)
        except Exception as exc:
            raise ConnectorParseError(
                f"Failed to validate Greenhouse API response: {exc}",
                source_type=self.source_type,
            ) from exc

        normalized_jobs: List[NormalizedJob] = []
        for raw_job in payload.jobs:
            normalized_job = GreenhouseParser.parse_job(raw_job)
            normalized_jobs.append(normalized_job)

        logger.info(
            "Successfully fetched and normalized %d Greenhouse jobs for board '%s'",
            len(normalized_jobs),
            self.board_token,
        )
        return normalized_jobs
