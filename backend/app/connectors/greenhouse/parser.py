"""Parser and normalizer for Greenhouse jobs."""

from datetime import timezone
import html
import re
from typing import Optional

from app.connectors.exceptions import ConnectorParseError
from app.connectors.greenhouse.schemas import GreenhouseJob
from app.connectors.models import NormalizedJob


def normalize_employment_type(text: Optional[str]) -> Optional[str]:
    """Map common textual designations to standard employment_type tokens."""
    if not text:
        return None
    val = text.lower()
    if "full" in val and "time" in val:
        return "full_time"
    if "part" in val and "time" in val:
        return "part_time"
    if "contract" in val or "temporary" in val:
        return "contract"
    if "intern" in val:
        return "internship"
    return None


def normalize_workplace_type(location: Optional[str], title: Optional[str]) -> Optional[str]:
    """Map location or title keywords to standardized workplace models."""
    combined = f"{location or ''} {title or ''}".lower()
    if "remote" in combined:
        return "remote"
    if "hybrid" in combined:
        return "hybrid"
    if "on-site" in combined or "onsite" in combined:
        return "onsite"
    return None


def clean_html_description(raw_html: Optional[str]) -> Optional[str]:
    """Basic normalization for job descriptions while preserving content structure."""
    if not raw_html:
        return None
    # Unescape HTML entities (e.g., &amp; -> &, &lt; -> <)
    text = html.unescape(raw_html)
    # Strip dangerous script or iframe tags if present
    text = re.sub(r"<(script|iframe|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip() or None


class GreenhouseParser:
    """Transforms raw Greenhouse schema representations into canonical NormalizedJob models."""

    @staticmethod
    def parse_job(raw: GreenhouseJob) -> NormalizedJob:
        """Normalize a single GreenhouseJob."""
        try:
            loc_str = raw.location.name.strip() if raw.location and raw.location.name else None

            # Detect employment type from metadata if available
            emp_type = None
            if raw.metadata:
                for item in raw.metadata:
                    if item.name and "employment" in item.name.lower():
                        emp_type = normalize_employment_type(str(item.value))
                        break
            if not emp_type:
                emp_type = normalize_employment_type(raw.title)

            workplace = normalize_workplace_type(loc_str, raw.title)

            # Ensure posted_at is timezone-aware UTC
            posted_at_utc = None
            if raw.updated_at:
                posted_at_utc = (
                    raw.updated_at
                    if raw.updated_at.tzinfo
                    else raw.updated_at.replace(tzinfo=timezone.utc)
                )

            return NormalizedJob(
                external_id=str(raw.id),
                title=raw.title.strip(),
                description=clean_html_description(raw.content),
                location=loc_str,
                employment_type=emp_type,
                workplace_type=workplace,
                application_url=raw.absolute_url,
                source_url=raw.absolute_url,
                posted_at=posted_at_utc,
                raw_metadata={
                    "departments": [d.name for d in raw.departments or [] if d.name],
                },
            )
        except Exception as exc:
            raise ConnectorParseError(
                f"Failed to normalize Greenhouse job (id={raw.id}): {exc}",
                source_type="greenhouse",
            ) from exc

    @classmethod
    def parse_jobs_response(cls, data: object) -> list[NormalizedJob]:
        """Parse raw Greenhouse jobs payload dictionary into list of NormalizedJob."""
        if not isinstance(data, dict):
            return []
        raw_jobs = data.get("jobs", [])
        if not isinstance(raw_jobs, list):
            return []

        jobs: list[NormalizedJob] = []
        for raw in raw_jobs:
            try:
                job = GreenhouseJob.model_validate(raw)
                jobs.append(cls.parse_job(job))
            except Exception:
                continue
        return jobs
