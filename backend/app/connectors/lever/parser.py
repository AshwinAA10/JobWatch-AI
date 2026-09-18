"""Parser and normalizer for Lever job postings."""

from datetime import datetime, timezone
from typing import Optional

from app.connectors.exceptions import ConnectorParseError
from app.connectors.greenhouse.parser import (
    clean_html_description,
    normalize_employment_type,
    normalize_workplace_type,
)
from app.connectors.lever.schemas import LeverPosting
from app.connectors.models import NormalizedJob


class LeverParser:
    """Transforms raw Lever schema representations into canonical NormalizedJob models."""

    @staticmethod
    def parse_posting(raw: LeverPosting) -> NormalizedJob:
        """Normalize a single LeverPosting."""
        try:
            loc_str = None
            emp_type = None
            if raw.categories:
                loc_str = raw.categories.location
                emp_type = normalize_employment_type(raw.categories.commitment)

            if not loc_str and raw.country:
                loc_str = raw.country

            if not emp_type:
                emp_type = normalize_employment_type(raw.text)

            workplace = None
            if raw.workplaceType:
                workplace = normalize_workplace_type(raw.workplaceType, raw.text)
            else:
                workplace = normalize_workplace_type(loc_str, raw.text)

            # Lever createdAt is in milliseconds since unix epoch
            posted_at_utc = None
            if raw.createdAt:
                posted_at_utc = datetime.fromtimestamp(
                    raw.createdAt / 1000.0,
                    tz=timezone.utc,
                )

            # Combine description and additional notes if present
            desc = clean_html_description(raw.description) or raw.descriptionPlain
            if raw.additional or raw.additionalPlain:
                extra = clean_html_description(raw.additional) or raw.additionalPlain
                desc = f"{desc}\n\n{extra}" if desc else extra

            return NormalizedJob(
                external_id=raw.id,
                title=raw.text.strip(),
                description=desc,
                location=loc_str.strip() if loc_str else None,
                employment_type=emp_type,
                workplace_type=workplace,
                application_url=raw.applyUrl or raw.hostedUrl,
                source_url=raw.hostedUrl,
                posted_at=posted_at_utc,
                raw_metadata={
                    "team": raw.categories.team if raw.categories else None,
                    "department": raw.categories.department if raw.categories else None,
                },
            )
        except Exception as exc:
            raise ConnectorParseError(
                f"Failed to normalize Lever posting (id={raw.id}): {exc}",
                source_type="lever",
            ) from exc

    @classmethod
    def parse_postings_response(cls, data: object) -> list[NormalizedJob]:
        """Parse raw Lever postings payload array into list of NormalizedJob."""
        if not isinstance(data, list):
            return []

        jobs: list[NormalizedJob] = []
        for raw_item in data:
            try:
                posting = LeverPosting.model_validate(raw_item)
                jobs.append(cls.parse_posting(posting))
            except Exception:
                continue
        return jobs
