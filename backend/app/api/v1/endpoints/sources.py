"""Career Source ingestion and synchronization endpoints (Development / Testing)."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.connectors.exceptions import ConnectorConfigurationError, ConnectorError
from app.core.database import get_db
from app.services.ingestion import IngestionResult, JobIngestionService

router = APIRouter()


@router.post(
    "/sources/{source_id}/sync",
    response_model=IngestionResult,
    summary="Trigger Manual Source Ingestion (Development / Test)",
    description="Extracts, normalizes, and persists all active jobs from the target CareerSource. Provided for Phase 2 testing.",
    tags=["Career Sources"],
)
async def sync_career_source(
    source_id: UUID,
    db: Session = Depends(get_db),
) -> IngestionResult:
    """Trigger manual job extraction and persistence for a CareerSource."""
    service = JobIngestionService(db)
    try:
        return await service.ingest_source(source_id)
    except ConnectorConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
