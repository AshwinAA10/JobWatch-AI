"""Workday Career Site (CXS API) connector."""

import logging
import re
from typing import List, Tuple
from urllib.parse import urlparse

from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import ConnectorConfigurationError, ConnectorParseError
from app.connectors.models import NormalizedJob
from app.connectors.workday.parser import WorkdayParser
from app.connectors.workday.schemas import WorkdaySearchResponse

logger = logging.getLogger("jobwatch.connectors.workday")

WORKDAY_PAGE_LIMIT = 20
MAX_OFFSET_LIMIT = 5000


def parse_workday_url(base_url: str) -> Tuple[str, str, str]:
    """Extract (host, tenant, site) from a Workday career portal URL.
    
    Examples:
        'https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite' -> ('nvidia.wd5.myworkdayjobs.com', 'nvidia', 'NVIDIAExternalCareerSite')
        'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced' -> ('adobe.wd5.myworkdayjobs.com', 'adobe', 'external_experienced')
        'https://myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite' -> ('myworkdayjobs.com', 'nvidia', 'NVIDIAExternalCareerSite')
    """
    if not base_url or not isinstance(base_url, str):
        raise ConnectorConfigurationError(
            "Workday base_url is required",
            source_type="workday",
        )

    parsed = urlparse(base_url.strip())
    host = parsed.netloc
    path = parsed.path.strip("/")

    if not host:
        raise ConnectorConfigurationError(
            f"Invalid Workday URL: missing host in '{base_url}'",
            source_type="workday",
        )

    # Check for direct wday/cxs/ path
    cxs_match = re.search(r"wday/cxs/([^/]+)/([^/]+)", path)
    if cxs_match:
        tenant, site = cxs_match.group(1), cxs_match.group(2)
        return host, tenant, site

    # Extract tenant from subdomain (e.g., 'nvidia' from 'nvidia.wd5.myworkdayjobs.com')
    host_parts = host.split(".")
    tenant = host_parts[0] if len(host_parts) >= 3 else ""

    # Path might contain locale prefix like 'en-US/{site}' or just '{site}'
    path_segments = [p for p in path.split("/") if p and not re.match(r"^[a-z]{2}-[A-Z]{2}$", p)]
    site = path_segments[0] if path_segments else ""

    if not tenant or not site:
        raise ConnectorConfigurationError(
            f"Could not derive Workday tenant and site from '{base_url}'. "
            "Expected format: 'https://{tenant}.wdX.myworkdayjobs.com/en-US/{site}'",
            source_type="workday",
        )

    return host, tenant, site


class WorkdayConnector(BaseJobConnector):
    """Connector for querying Workday public Candidate Experience (CXS) search API."""

    source_type: str = "workday"

    def validate_source_config(self) -> None:
        """Validate that host, tenant, and site can be derived."""
        self.host, self.tenant, self.site = parse_workday_url(self.source.base_url)

    async def fetch_jobs(self) -> List[NormalizedJob]:
        """Fetch and normalize all active jobs from the Workday site with pagination."""
        endpoint = f"https://{self.host}/wday/cxs/{self.tenant}/{self.site}/jobs"
        normalized_jobs: List[NormalizedJob] = []

        offset = 0
        total = None

        logger.info(
            "Fetching Workday jobs for tenant='%s', site='%s' (source_id=%s)",
            self.tenant,
            self.site,
            self.source.id,
        )

        while offset < MAX_OFFSET_LIMIT:
            payload = {
                "appliedFacets": {},
                "limit": WORKDAY_PAGE_LIMIT,
                "offset": offset,
                "searchText": "",
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            data = await self.http.post_json(endpoint, json=payload, headers=headers)

            try:
                search_res = WorkdaySearchResponse.model_validate(data)
            except Exception as exc:
                raise ConnectorParseError(
                    f"Failed to validate Workday search response: {exc}",
                    source_type=self.source_type,
                ) from exc

            total = search_res.total
            postings = search_res.jobPostings

            if not postings:
                break

            for posting in postings:
                normalized = WorkdayParser.parse_posting(
                    posting,
                    host=self.host,
                    site=self.site,
                )
                normalized_jobs.append(normalized)

            offset += len(postings)
            if offset >= total:
                break

        logger.info(
            "Successfully fetched and normalized %d Workday jobs for tenant '%s'",
            len(normalized_jobs),
            self.tenant,
        )
        return normalized_jobs
