"""Parser and normalizer for Workday job postings."""

import re
from typing import Optional

from app.connectors.exceptions import ConnectorParseError
from app.connectors.greenhouse.parser import (
    normalize_employment_type,
    normalize_workplace_type,
)
from app.connectors.models import NormalizedJob
from app.connectors.workday.schemas import WorkdayJobPosting, WorkdaySearchResponse


def extract_external_id(raw: WorkdayJobPosting) -> str:
    """Derive external ATS job ID from bulletFields or externalPath.
    
    Examples:
        bulletFields: ['JR102938'] -> 'JR102938'
        externalPath: '/job/USA-CA/Software-Engineer_JR102938' -> 'JR102938'
    """
    if raw.bulletFields and raw.bulletFields[0].strip():
        return raw.bulletFields[0].strip()

    # Fallback to extracting requisition identifier at the end of the path
    match = re.search(r"_([A-Za-z0-9-]+)$", raw.externalPath)
    if match:
        return match.group(1)

    return raw.externalPath.strip("/")


class WorkdayParser:
    """Transforms raw Workday schema representations into canonical NormalizedJob models."""

    def __init__(self, host: str = "", tenant: str = "", site: str = "") -> None:
        self.host = host
        self.tenant = tenant
        self.site = site

    @staticmethod
    def parse_posting(raw: WorkdayJobPosting, host: str, site: str) -> NormalizedJob:
        """Normalize a single WorkdayJobPosting."""
        try:
            external_id = extract_external_id(raw)
            loc_str = raw.locationsText.strip() if raw.locationsText else None
            emp_type = normalize_employment_type(raw.timeType) or normalize_employment_type(raw.title)
            workplace = normalize_workplace_type(loc_str, raw.title)

            # Ensure host does not have scheme
            clean_host = host.replace("http://", "").replace("https://", "").strip("/")
            clean_path = raw.externalPath if raw.externalPath.startswith("/") else f"/{raw.externalPath}"
            job_url = f"https://{clean_host}/en-US/{site}{clean_path}"

            return NormalizedJob(
                external_id=external_id,
                title=raw.title.strip(),
                description=None,  # Workday search API only provides summary bullet fields
                location=loc_str,
                employment_type=emp_type,
                workplace_type=workplace,
                application_url=job_url,
                source_url=job_url,
                posted_at=None,  # Workday uses relative strings ("Posted 3 Days Ago"); per spec do not fabricate dates
                raw_metadata={
                    "postedOn": raw.postedOn,
                    "bulletFields": raw.bulletFields,
                },
            )
        except Exception as exc:
            raise ConnectorParseError(
                f"Failed to normalize Workday job posting '{raw.title}': {exc}",
                source_type="workday",
            ) from exc

    def parse_search_response(self, data: object) -> list[NormalizedJob]:
        """Parse raw Workday search response dictionary into list of NormalizedJob."""
        if not isinstance(data, dict):
            return []
        raw_postings = data.get("jobPostings", [])
        if not isinstance(raw_postings, list):
            return []

        jobs: list[NormalizedJob] = []
        for raw in raw_postings:
            try:
                posting = WorkdayJobPosting.model_validate(raw)
                jobs.append(self.parse_posting(posting, self.host, self.site))
            except Exception:
                continue
        return jobs
