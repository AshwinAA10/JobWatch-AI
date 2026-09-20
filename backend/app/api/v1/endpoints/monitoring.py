"""Monitoring Engine API endpoints (Phase 3)."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.monitoring_run import MonitoringTriggerType
from app.monitoring.exceptions import (
    SourceAlreadyRunningError,
    SourceInactiveError,
    SourceNotFoundError,
)
from app.monitoring.executor import MonitoringExecutor
from app.monitoring.scheduler import MonitoringScheduler, get_scheduler
from app.monitoring.schemas import (
    MonitoringBatchTriggerResponse,
    MonitoringRunRead,
    MonitoringStatusResponse,
    MonitoringTriggerResponse,
)
from app.repositories.career_source import CareerSourceRepository
from app.repositories.monitoring_run import MonitoringRunRepository

router = APIRouter()
settings = get_settings()


@router.get(
    "/status",
    response_model=MonitoringStatusResponse,
    summary="Get Monitoring Scheduler Status",
    description="Inspect whether the background monitoring engine is active, its interval, concurrency, and current running state.",
)
def get_monitoring_status(
    scheduler: MonitoringScheduler = Depends(get_scheduler),
) -> MonitoringStatusResponse:
    """Return the operational state of the monitoring scheduler."""
    return MonitoringStatusResponse(
        enabled=scheduler.is_enabled,
        running=scheduler.is_running,
        interval_seconds=scheduler.interval_seconds,
        max_concurrency=settings.MONITORING_MAX_CONCURRENCY,
        active_sources_count=scheduler.executor.get_active_sources_count(),
        last_run_at=scheduler.last_run_at,
        next_run_at=scheduler.next_run_at,
    )


@router.post(
    "/run/{source_id}",
    response_model=MonitoringTriggerResponse,
    summary="Trigger Manual Source Monitoring Run",
    description="Manually trigger a monitoring execution for a specific CareerSource. Concurrency and same-source locks apply.",
)
async def trigger_source_run(
    source_id: UUID,
    db: Session = Depends(get_db),
    scheduler: MonitoringScheduler = Depends(get_scheduler),
) -> MonitoringTriggerResponse:
    """Trigger a manual monitoring run for a specific source."""
    source_repo = CareerSourceRepository(db)
    source = source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CareerSource with ID '{source_id}' not found",
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CareerSource '{source.name}' ({source_id}) is inactive",
        )

    run, message = await scheduler.executor.execute_source(
        source_id=source_id,
        trigger_type=MonitoringTriggerType.MANUAL.value,
    )

    if run is None:
        return MonitoringTriggerResponse(
            source_id=source_id,
            run_id=None,
            status="SKIPPED",
            message=message,
        )

    return MonitoringTriggerResponse(
        source_id=source_id,
        run_id=run.id,
        status=run.status,
        message=message,
    )


@router.post(
    "/run-all",
    response_model=MonitoringBatchTriggerResponse,
    summary="Trigger Manual Run for All Active Sources",
    description="Manually triggers monitoring for all active career sources concurrently.",
)
async def trigger_all_sources_run(
    scheduler: MonitoringScheduler = Depends(get_scheduler),
) -> MonitoringBatchTriggerResponse:
    """Trigger a manual monitoring cycle across all active sources."""
    results = await scheduler.trigger_cycle(
        trigger_type=MonitoringTriggerType.MANUAL.value,
    )

    triggered_ids = [s_id for s_id, run, _ in results if run is not None]
    skipped_ids = [s_id for s_id, run, _ in results if run is None]

    return MonitoringBatchTriggerResponse(
        triggered_count=len(triggered_ids),
        skipped_count=len(skipped_ids),
        sources_triggered=triggered_ids,
        sources_skipped=skipped_ids,
        message=f"Dispatched monitoring for {len(triggered_ids)} sources ({len(skipped_ids)} skipped/locked).",
    )


@router.get(
    "/runs",
    response_model=List[MonitoringRunRead],
    summary="List Monitoring Run History",
    description="Query historical monitoring runs with optional filtering by source ID and status.",
)
def list_monitoring_runs(
    career_source_id: Optional[UUID] = Query(None, description="Filter by career source UUID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by run status"),
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
) -> List[MonitoringRunRead]:
    """Return historical monitoring runs ordered by newest first."""
    run_repo = MonitoringRunRepository(db)
    runs = run_repo.list_runs(
        career_source_id=career_source_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return [MonitoringRunRead.model_validate(r) for r in runs]
