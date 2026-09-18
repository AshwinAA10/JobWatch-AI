"""Job ingestion orchestration service."""

import logging
import time
from typing import List, Optional
from uuid import UUID
import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.connectors.exceptions import (
    ConnectorConfigurationError,
    ConnectorError,
)
from app.connectors.factory import ConnectorFactory
from app.connectors.http import ConnectorHttpClient
from app.models.career_source import CareerSource
from app.repositories.career_source import CareerSourceRepository
from app.repositories.job import JobRepository
from app.schemas.job import JobCreate

logger = logging.getLogger("jobwatch.services.ingestion")


class IngestionResult(BaseModel):
    """Structured report returned by the ingestion service after processing a career source."""

    model_config = ConfigDict(extra="ignore")

    source_id: UUID = Field(..., description="ID of the ingested career source")
    company_id: UUID = Field(..., description="ID of the parent company")
    source_type: str = Field(..., description="Connector provider type (e.g. greenhouse, lever, workday)")
    jobs_fetched: int = Field(0, description="Total normalized jobs returned by connector")
    jobs_persisted: int = Field(0, description="New job records inserted into database")
    jobs_updated: int = Field(0, description="Existing job records updated and refreshed")
    jobs_skipped: int = Field(0, description="Jobs skipped due to validation or processing issues")
    errors: List[str] = Field(default_factory=list, description="Diagnostic summaries of any partial failures")
    duration_seconds: float = Field(..., description="Elapsed execution time in seconds")


class JobIngestionService:
    """Service that coordinates career portal job extraction, normalization, and persistence.
    
    Acts as the primary bridge between connector implementations and the persistence layer.
    The future monitoring engine (Phase 3) will schedule and dispatch through this service.
    """

    def __init__(
        self,
        db: Session,
        http_client: Optional[ConnectorHttpClient] = None,
        raw_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.db = db
        self.source_repo = CareerSourceRepository(db)
        self.job_repo = JobRepository(db)
        self.http_client = http_client
        self.raw_client = raw_client

    async def ingest_source(self, source_id: UUID) -> IngestionResult:
        """Fetch and persist all active jobs for a given CareerSource ID.
        
        Args:
            source_id: UUID of the target CareerSource.
            
        Returns:
            IngestionResult summary detailing counts and timing.
            
        Raises:
            ConnectorConfigurationError: If source does not exist or is marked inactive.
            ConnectorError: If connector execution encounters a fatal provider failure.
        """
        source = self.source_repo.get_by_id(source_id)
        if source is None:
            raise ConnectorConfigurationError(
                f"CareerSource with ID '{source_id}' does not exist",
            )
        return await self.ingest_source_instance(source)

    async def ingest_source_instance(self, source: CareerSource) -> IngestionResult:
        """Fetch and persist all active jobs for an in-memory CareerSource instance."""
        if not source.is_active:
            raise ConnectorConfigurationError(
                f"CareerSource '{source.name}' ({source.id}) is inactive",
                source_type=source.source_type,
            )

        start_time = time.perf_counter()
        connector = ConnectorFactory.create(
            source=source,
            http_client=self.http_client,
            raw_client=self.raw_client,
        )

        logger.info(
            "Starting ingestion for source '%s' (type=%s, id=%s)",
            source.name,
            source.source_type,
            source.id,
        )

        try:
            normalized_jobs = await connector.fetch_jobs()
        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(
                f"Unexpected error during job extraction: {exc}",
                source_type=source.source_type,
            ) from exc

        persisted_count = 0
        updated_count = 0
        skipped_count = 0
        errors: List[str] = []

        for item in normalized_jobs:
            try:
                job_in = JobCreate(
                    company_id=source.company_id,
                    career_source_id=source.id,
                    external_id=item.external_id,
                    title=item.title,
                    description=item.description,
                    location=item.location,
                    employment_type=item.employment_type,
                    workplace_type=item.workplace_type,
                    application_url=item.application_url,
                    source_url=item.source_url,
                    posted_at=item.posted_at,
                    is_active=True,
                )
                _, created = self.job_repo.upsert(job_in)
                if created:
                    persisted_count += 1
                else:
                    updated_count += 1
            except Exception as exc:
                skipped_count += 1
                error_msg = f"Failed to persist job '{item.title}' (external_id={item.external_id}): {exc}"
                logger.error(error_msg)
                errors.append(error_msg)

        elapsed = round(time.perf_counter() - start_time, 3)

        result = IngestionResult(
            source_id=source.id,
            company_id=source.company_id,
            source_type=source.source_type,
            jobs_fetched=len(normalized_jobs),
            jobs_persisted=persisted_count,
            jobs_updated=updated_count,
            jobs_skipped=skipped_count,
            errors=errors,
            duration_seconds=elapsed,
        )

        logger.info(
            "Ingestion completed for source '%s': %d fetched, %d created, %d updated in %.3fs",
            source.name,
            result.jobs_fetched,
            result.jobs_persisted,
            result.jobs_updated,
            result.duration_seconds,
        )
        return result
