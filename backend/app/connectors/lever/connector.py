"""Lever Postings API connector."""

import logging
import re
from typing import List
from urllib.parse import urlparse

from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import ConnectorConfigurationError, ConnectorParseError
from app.connectors.lever.parser import LeverParser
from app.connectors.lever.schemas import LeverPosting
from app.connectors.models import NormalizedJob

logger = logging.getLogger("jobwatch.connectors.lever")

LEVER_API_BASE = "https://api.lever.co/v0/postings"
PAGE_LIMIT = 100
MAX_PAGES = 50


def extract_lever_site(base_url: str) -> str:
    """Extract the Lever site identifier from a URL or raw slug.
    
    Examples:
        'https://jobs.lever.co/netflix' -> 'netflix'
        'https://api.lever.co/v0/postings/netflix' -> 'netflix'
        'netflix' -> 'netflix'
    """
    if not base_url or not isinstance(base_url, str):
        raise ConnectorConfigurationError(
            "Lever base_url is required",
            source_type="lever",
        )

    clean_url = base_url.strip().rstrip("/")
    if "/" not in clean_url:
        site = clean_url
    else:
        parsed = urlparse(clean_url)
        path = parsed.path.strip("/")
        # Path might be: 'v0/postings/{site}' or '{site}'
        match = re.search(r"(?:postings/)?([^/]+)$", path)
        if match and match.group(1):
            site = match.group(1)
        else:
            site = path.split("/")[-1]

    if not site or site in {"postings", "v0", "jobs"}:
        raise ConnectorConfigurationError(
            f"Could not extract valid Lever site identifier from '{base_url}'",
            source_type="lever",
        )
    return site


class LeverConnector(BaseJobConnector):
    """Connector for querying Lever Postings API."""

    source_type: str = "lever"

    def validate_source_config(self) -> None:
        """Validate that the Lever site identifier can be extracted."""
        self.site = extract_lever_site(self.source.base_url)

    async def fetch_jobs(self) -> List[NormalizedJob]:
        """Fetch and normalize all active jobs from the Lever site with pagination."""
        endpoint = f"{LEVER_API_BASE}/{self.site}"
        normalized_jobs: List[NormalizedJob] = []

        skip = 0
        page = 0

        logger.info(
            "Fetching Lever jobs for site '%s' (source_id=%s)",
            self.site,
            self.source.id,
        )

        while page < MAX_PAGES:
            page += 1
            params = {
                "mode": "json",
                "limit": PAGE_LIMIT,
                "skip": skip,
            }

            data = await self.http.get_json(endpoint, params=params)

            if not isinstance(data, list):
                raise ConnectorParseError(
                    f"Expected list from Lever API, received {type(data).__name__}",
                    source_type=self.source_type,
                )

            if not data:
                break

            for item in data:
                try:
                    posting = LeverPosting.model_validate(item)
                    normalized_job = LeverParser.parse_posting(posting)
                    normalized_jobs.append(normalized_job)
                except Exception as exc:
                    raise ConnectorParseError(
                        f"Failed to parse Lever posting: {exc}",
                        source_type=self.source_type,
                    ) from exc

            # If fewer items than the requested limit were returned, we have reached the end
            if len(data) < PAGE_LIMIT:
                break

            skip += len(data)

        logger.info(
            "Successfully fetched and normalized %d Lever jobs for site '%s' across %d pages",
            len(normalized_jobs),
            self.site,
            page,
        )
        return normalized_jobs
