# JobWatch AI — Connector & Job Ingestion Architecture

This document specifies the design, implementation, configuration, and extension guidelines for the **JobWatch AI Phase 2 Connector Layer**.

---

## 1. Architectural Overview

The connector architecture provides a provider-independent ingestion pipeline that isolates third-party Applicant Tracking System (ATS) structures from JobWatch AI core domain logic.

The future Monitoring Engine (Phase 3) interacts strictly through the connector abstraction without knowing which career platform produced a job:

```text
                 ┌────────────────────┐
                 │    CareerSource    │
                 │    (PostgreSQL)    │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │  ConnectorFactory  │
                 └─────────┬──────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     Greenhouse          Lever          Workday
     Connector         Connector       Connector
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                 ┌────────────────────┐
                 │   NormalizedJob    │
                 │     (Unified)      │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Ingestion Service  │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │   JobRepository    │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │     PostgreSQL     │
                 └────────────────────┘
```

---

## 2. Core Abstractions

### 2.1 NormalizedJob Contract (`backend/app/connectors/models.py`)

A standardized representation across all providers:

| Field | Type | Description |
| :--- | :--- | :--- |
| `external_id` | `str` | Provider ATS requisition identifier (e.g. `4829101`, `JR-102938`) |
| `title` | `str` | Sanitized job title |
| `description` | `str \| None` | HTML-sanitized or plain text job description |
| `location` | `str \| None` | Location string (e.g. `"San Francisco, CA"`, `"Remote"`) |
| `employment_type` | `str \| None` | Normalized semantic token (`"full_time"`, `"part_time"`, `"contract"`, `"internship"`) |
| `workplace_type` | `str \| None` | Normalized workplace type (`"remote"`, `"hybrid"`, `"onsite"`) |
| `application_url` | `str` | Direct URL to application or candidate application form |
| `source_url` | `str \| None` | Hosted public listing URL |
| `posted_at` | `datetime \| None` | Timezone-aware UTC timestamp (never fabricated if omitted) |
| `raw_metadata` | `dict[str, Any]` | Provider-specific ancillary attributes (e.g. departments, teams) |

### 2.2 BaseJobConnector (`backend/app/connectors/base.py`)

All connectors inherit from `BaseJobConnector(ABC)`:
- `validate_source_config()`: Enforces URL format and provider-specific tokens on instantiation.
- `async fetch_jobs() -> List[NormalizedJob]`: Dispatches asynchronous HTTP calls and invokes parsers.
- `aclose()`: Releases underlying HTTP client resources.

### 2.3 ConnectorHttpClient (`backend/app/connectors/http.py`)

A production-grade HTTP client built on `httpx.AsyncClient`:
- **Timeout Configuration**: Dedicated connect (10s), read (25s), write (10s), and pool (10s) timeouts.
- **SSRF & URL Validation**: Restricts schemes strictly to `http` / `https`, blocks empty hosts, and prevents arbitrary file system access (`file://`).
- **Bounded Retries**: Automatically retries transient failures (`429`, `502`, `503`, `504`) using exponential backoff with jitter.
- **Non-Retryable Errors**: Immediately maps `400`, `401`, `403`, and `404` to `ConnectorConfigurationError` or `ConnectorResponseError`.
- **Rate-Limit Handling**: Parses `Retry-After` HTTP headers (capped at 10 seconds).

---

## 3. Supported Connectors

### 3.1 Greenhouse (`greenhouse`)
- **API Endpoint**: `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- **Supported `base_url` Formats**:
  - `https://boards.greenhouse.io/{board_token}`
  - `https://job-boards.greenhouse.io/{board_token}`
  - `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs`
- **Normalization**: Extracts requisition IDs, unescapes and cleans HTML description tags, normalizes workplace types (`remote`, `hybrid`, `onsite`), and converts ISO-8601 timestamps to timezone-aware UTC.

### 3.2 Lever (`lever`)
- **API Endpoint**: `https://api.lever.co/v0/postings/{site}?mode=json`
- **Supported `base_url` Formats**:
  - `https://jobs.lever.co/{site}`
  - `https://api.lever.co/v0/postings/{site}`
- **Pagination**: Implements `skip` and `limit` paging (100 postings per batch) with infinite loop safeguards.
- **Normalization**: Converts epoch millisecond timestamps (`createdAt`) to timezone-aware UTC, extracts workplace classifications, and parses commitment categories into employment types.

### 3.3 Workday (`workday`)
- **API Endpoint**: `https://{host}/wday/cxs/{tenant}/{site}/jobs` (CXS POST)
- **Supported `base_url` Formats**:
  - `https://{tenant}.wd{x}.myworkdayjobs.com/en-US/{site}`
  - `https://{tenant}.myworkdayjobs.com/{site}`
  - `https://{host}/wday/cxs/{tenant}/{site}`
- **Pagination**: Implements `offset` and `limit` paging querying candidate experience search endpoints until `total` records are exhausted.
- **Normalization**: Extracts requisition IDs from `bulletFields` (e.g. `"JR-102938"`) or requisition paths, constructs canonical deep links, and normalizes time types.

---

## 4. Ingestion Service & Persistence

The `JobIngestionService` (`backend/app/services/ingestion.py`) orchestrates end-to-end ingestion:
1. Loads the active `CareerSource` from `CareerSourceRepository`.
2. Resolves the appropriate connector via `ConnectorFactory`.
3. Invokes `connector.fetch_jobs()` to retrieve normalized jobs.
4. Performs safe upserts via `JobRepository.upsert()` against the PostgreSQL composite unique index `(career_source_id, external_id)`:
   - New jobs are inserted with `first_seen_at = now()` and `last_seen_at = now()`.
   - Existing jobs update mutable fields and refresh `last_seen_at = now()`.
5. Returns a structured `IngestionResult` tracking fetched, created, updated, and skipped counts with total duration.

---

## 5. Adding a New Connector

To add a new ATS provider (e.g. `smartrecruiters`):

1. **Create Provider Directory**:
   ```text
   backend/app/connectors/smartrecruiters/
   ├── __init__.py
   ├── schemas.py
   ├── parser.py
   └── connector.py
   ```
2. **Define Provider Schemas** (`schemas.py`):
   Declare Pydantic models with `extra="ignore"` matching the external API response payload.
3. **Implement Parser** (`parser.py`):
   Convert provider schemas into `NormalizedJob` instances. Do not make network calls inside the parser.
4. **Implement Connector** (`connector.py`):
   Inherit from `BaseJobConnector`. Implement `validate_source_config()` and `fetch_jobs()`.
5. **Register in Registry** (`backend/app/connectors/__init__.py`):
   ```python
   registry.register("smartrecruiters", SmartRecruitersConnector)
   ```
6. **Add Fixtures & Tests**:
   - Add sample JSON fixture to `backend/tests/fixtures/smartrecruiters/`.
   - Add parser tests in `backend/tests/connectors/test_parsers.py`.
   - Add connector test to `test_connectors.py` and register in `test_contract.py`.
