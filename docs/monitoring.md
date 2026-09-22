# JobWatch AI — Monitoring Engine (Phase 3)

The **Monitoring Engine** automates career portal polling by executing scheduled and on-demand ingestion runs across registered `CareerSource` records, enforcing bounded concurrency, isolating failures, avoiding overlapping runs on identical sources, and recording comprehensive historical metrics in PostgreSQL.

---

## 1. Core Architectural Principle

Phase 3 enforces strict separation of responsibilities:

```text
Scheduler  ≠  Monitoring Executor  ≠  Monitoring Service  ≠  Connector  ≠  Ingestion Service
```

```text
┌──────────────────────────────────────────────┐
│              MonitoringScheduler             │
│            (Decides WHEN to poll)            │
└──────────────────────┬───────────────────────┘
                       │ Periodic cycle / Manual trigger
                       ▼
┌──────────────────────────────────────────────┐
│              MonitoringExecutor              │
│       (Manages CONCURRENCY & LOCKS)          │
└──────────────────────┬───────────────────────┘
                       │ Dispatches active sources
                       ▼
┌──────────────────────────────────────────────┐
│              MonitoringService               │
│          (Decides WHAT & HOW to run)         │
└──────────────────────┬───────────────────────┘
                       │ Transient retries & timeout
                       ▼
┌──────────────────────────────────────────────┐
│              JobIngestionService             │
│          (Decides HOW to ingest & save)      │
└──────────────────────┬───────────────────────┘
                       │ Retrieves & normalizes
                       ▼
┌──────────────────────────────────────────────┐
│           Career Portal Connectors           │
│         (Greenhouse, Lever, Workday)         │
└──────────────────────────────────────────────┘
```

1. **`MonitoringScheduler`**: Asynchronous in-process task running on FastAPI lifespan. Manages intervals and start/stop lifecycle.
2. **`MonitoringExecutor`**: Enforces system-wide concurrency limits (`asyncio.Semaphore`), eliminates concurrent executions for the same source (`_active_sources` set & active DB query), and isolates errors across distinct sources using `asyncio.gather`.
3. **`MonitoringService`**: Manages execution state transitions (`PENDING` -> `RUNNING` -> `SUCCESS` / `PARTIAL_SUCCESS` / `FAILED`), handles bounded exponential backoff retries on transient errors, enforces source timeouts, and persists execution history.
4. **`JobIngestionService`**: Phase 2 ingestion pipeline that fetches via `ConnectorFactory`, normalizes, and upserts jobs via `JobRepository`.

---

## 2. Monitoring Run State Machine

Every monitoring attempt is captured in the `monitoring_runs` database table.

```text
               ┌──────────┐
               │ PENDING  │
               └────┬─────┘
                    │ mark_running()
                    ▼
               ┌──────────┐
               │ RUNNING  │
               └────┬─────┘
         ┌──────────┼──────────────┬──────────────┐
         │          │              │              │
(all jobs ok) (some skipped) (fatal error)   (shutdown)
         ▼          ▼              ▼              ▼
    ┌─────────┐┌───────────┐ ┌──────────┐   ┌───────────┐
    │ SUCCESS ││  PARTIAL  │ │  FAILED  │   │ CANCELLED │
    │         ││  SUCCESS  │ │          │   │           │
    └─────────┘└───────────┘ └──────────┘   └───────────┘
```

### Transition Invariants
- `PENDING` -> `RUNNING`: Run is initialized and resources are being allocated.
- `RUNNING` -> `SUCCESS`: Connector fetched jobs and 100% of candidate records were successfully inserted or updated without skipped jobs or record errors.
- `RUNNING` -> `PARTIAL_SUCCESS`: The career portal was reached and valid jobs were persisted, but some individual records were skipped due to malformed payloads or schema validation.
- `RUNNING` -> `FAILED`: Unrecoverable connector error, exhausted retries, or execution timeout.
- Terminal statuses (`SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `CANCELLED`) are immutable for a given run ID. Re-executions generate a new `MonitoringRun` row.

---

## 3. Database Schema: `monitoring_runs`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | Primary Key | Unique execution identifier |
| `career_source_id` | `UUID` | Foreign Key (CASCADE) | Target `CareerSource` |
| `status` | `VARCHAR(32)` | Non-null, default `PENDING` | Current state machine status |
| `trigger_type` | `VARCHAR(32)` | Non-null, default `SCHEDULED` | `SCHEDULED` or `MANUAL` |
| `started_at` | `TIMESTAMPTZ` | Nullable | When status transitioned to `RUNNING` |
| `completed_at` | `TIMESTAMPTZ` | Nullable | When execution reached terminal state |
| `jobs_fetched` | `INTEGER` | Non-null, default 0 | Total jobs returned by connector |
| `jobs_created` | `INTEGER` | Non-null, default 0 | New jobs inserted into database |
| `jobs_updated` | `INTEGER` | Non-null, default 0 | Existing jobs refreshed in database |
| `jobs_skipped` | `INTEGER` | Non-null, default 0 | Records skipped due to parsing/validation issues |
| `error_count` | `INTEGER` | Non-null, default 0 | Number of caught errors/skipped items |
| `error_message` | `TEXT` | Nullable | Diagnostic summary of failure |
| `attempt` | `INTEGER` | Non-null, default 1 | Retry counter (1 = initial, 2+ = retries) |
| `created_at` | `TIMESTAMPTZ` | Non-null, default `now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Non-null, default `now()` | Last modification timestamp |

### Indexes
- `ix_monitoring_runs_career_source_id` on `career_source_id`
- `ix_monitoring_runs_status` on `status`
- `ix_monitoring_runs_created_at` on `created_at`
- `ix_monitoring_runs_source_started` composite on `(career_source_id, started_at)`

---

## 4. Concurrency & Overlap Protection

### Max Concurrency Limit
Configured via `MONITORING_MAX_CONCURRENCY` (default: 5). Controlled using an `asyncio.Semaphore`. When 10 sources are queued, at most 5 will actively execute HTTP requests and DB operations simultaneously.

### Same-Source Overlap Prevention
Prevents redundant concurrent scraping of the same career board:
1. **In-Memory Tracking**: `MonitoringExecutor` maintains an `_active_sources: Set[UUID]` protected by an `asyncio.Lock`. If source A is active and a new trigger requests source A, the second execution is immediately skipped with a descriptive message.
2. **Database State Verification**: The executor verifies whether any `MonitoringRun` is currently marked `RUNNING` for that `career_source_id`.

### Cross-Source Error Isolation
When executing a cycle over multiple sources, all jobs run concurrently via `asyncio.gather(*tasks, return_exceptions=False)` wrapped in individual exception guards. A failure, crash, or timeout in Source A will **never** stop or delay Source B or Source C.

---

## 5. Retry & Timeout Policies

### Error Classification
- **Permanent Errors (Non-Retryable)**:
  - `ConnectorConfigurationError`: Missing tokens, malformed board URLs.
  - `UnsupportedConnectorError`: Unknown ATS type.
  - `SourceInactiveError`: Source is disabled.
  - Failures are finalized immediately as `FAILED` on attempt 1.
- **Transient Errors (Retryable)**:
  - Upstream 5xx server errors, connection resets, network drops.
  - Retried up to `MONITORING_MAX_RETRIES` times with bounded exponential backoff (`MONITORING_RETRY_BACKOFF_SECONDS * attempt`).

### Execution Timeout
Bounded by `MONITORING_SOURCE_TIMEOUT_SECONDS` (default: 120s) using `asyncio.wait_for()`. If a remote portal hangs, the operation is aborted and marked `FAILED` with a timeout diagnosis.

---

## 6. Configuration Reference

| Environment Variable | Type | Default | Description |
|---|---|---|---|
| `MONITORING_ENABLED` | `bool` | `False` | Enable background scheduler loop |
| `MONITORING_INTERVAL_SECONDS` | `int` | `900` | Scheduled polling interval (15 min) |
| `MONITORING_MAX_CONCURRENCY` | `int` | `5` | Max simultaneous source executions |
| `MONITORING_MAX_RETRIES` | `int` | `2` | Max retry attempts for transient errors |
| `MONITORING_RETRY_BACKOFF_SECONDS` | `float` | `5.0` | Base backoff interval multiplier |
| `MONITORING_SOURCE_TIMEOUT_SECONDS` | `float` | `120.0` | Max duration per source run |

---

## 7. Scheduler Lifecycle & FastAPI Integration

Integrated cleanly using FastAPI's modern `lifespan` context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = get_scheduler()
    if scheduler.is_enabled:
        await scheduler.start()
    yield
    # Shutdown
    if scheduler.is_running:
        await scheduler.stop(timeout=10.0)
```

- When `MONITORING_ENABLED=False` (e.g. during test suites, CLI runs, or local debugging), no background tasks are created.
- On shutdown, `scheduler.stop()` signals the stop event, cancels the task, and awaits termination cleanly without leaving orphaned connections.

---

## 8. Development & Monitoring API

The API provides operational status inspection and manual triggers under `/api/v1/monitoring`.

> [!IMPORTANT]
> These endpoints do not require authentication in Phase 3 and are strictly intended for development, administration, and internal testing. They accept `career_source_id` references only (no arbitrary URLs).

### Endpoints

#### 1. `GET /api/v1/monitoring/status`
Returns scheduler operational state.
```json
{
  "enabled": true,
  "running": true,
  "interval_seconds": 900,
  "max_concurrency": 5,
  "active_sources_count": 0,
  "last_run_at": "2026-09-22T14:00:00Z",
  "next_run_at": "2026-09-22T14:15:00Z"
}
```

#### 2. `POST /api/v1/monitoring/run/{source_id}`
Manually trigger a run for a single source.
```json
{
  "source_id": "b1f868d4-51e8-4663-8a3d-4d43764d85e7",
  "run_id": "93699c27-3932-42b7-a3a2-63b7e7193630",
  "status": "SUCCESS",
  "message": "Execution completed with status SUCCESS"
}
```

#### 3. `POST /api/v1/monitoring/run-all`
Dispatches execution for all active career sources concurrently.
```json
{
  "triggered_count": 3,
  "skipped_count": 1,
  "sources_triggered": ["..."],
  "sources_skipped": ["..."],
  "message": "Dispatched monitoring for 3 sources (1 skipped/locked)."
}
```

#### 4. `GET /api/v1/monitoring/runs`
Query run history with optional filtering and pagination.
- Query parameters:
  - `career_source_id` (optional UUID)
  - `status` (optional: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `PENDING`, `RUNNING`)
  - `skip` (default: 0)
  - `limit` (default: 50, max: 200)

---

## 9. Multi-Worker Limitation & Scaling Strategy

> [!WARNING]
> **In-Process Scheduler Multi-Worker Warning:**
> In Phase 3, `MonitoringScheduler` runs directly inside the FastAPI backend process as an async background task.
> If the backend is scaled horizontally using multiple Uvicorn workers (e.g. `uvicorn --workers 4`), **each worker process will run its own internal scheduler instance**, leading to duplicate trigger attempts.
> 
> For Phase 3, this is mitigated within a single process via in-memory locking and database-level active run checks.
> For production distributed deployments (Phase 12), scheduling must be decoupled into a dedicated singleton worker or external scheduler (e.g., Celery Beat, Cloud Scheduler, or Kubernetes CronJob).
