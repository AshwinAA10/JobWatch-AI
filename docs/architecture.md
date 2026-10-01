# JobWatch AI — Architecture Specification

## 1. System Vision

JobWatch AI is an intelligent opportunity-monitoring platform designed to eliminate the friction of searching for careers across dispersed company career portals.

By connecting directly to target company portals, normalizing disparate job postings, running semantic similarity matching against user career profiles, and alerting users in real time, JobWatch AI ensures professionals never miss high-value opportunities.

---

## 2. High-Level Ingestion & Monitoring Architecture (Phase 3 Active)

```text
                         ┌─────────────────────┐
                         │ MonitoringScheduler │
                         └──────────┬──────────┘
                                    │ Periodic cycle / Manual trigger
                                    ▼
                         ┌─────────────────────┐
                         │ MonitoringExecutor  │
                         └──────────┬──────────┘
                                    │ Concurrency control & same-source locks
                                    ▼
                         ┌─────────────────────┐
                         │  MonitoringService  │
                         └──────────┬──────────┘
                                    │ Retry policy & run recording
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
               CareerSource A              CareerSource B
                      │                           │
                      ▼                           ▼
               ConnectorFactory            ConnectorFactory
                      │                           │
                      ▼                           ▼
            Greenhouse / Lever / Workday  Greenhouse / Lever / Workday
                      │                           │
                      └─────────────┬─────────────┘
                                    ▼
                         JobIngestionService
                                    │
                                    ▼
                              JobRepository
                                    │
                                    ▼
                               PostgreSQL
```

Monitoring history is recorded per execution attempt:

```text
CareerSource
     │
     └──────────────┐
                    ▼
              MonitoringRun
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
     SUCCESS     PARTIAL       FAILED
```

```text
                     ┌─────────────────┐
                     │    Scheduler    │
                     └────────┬────────┘
                              ↓
                     ┌─────────────────┐
                     │    Monitoring   │
                     │     Engine      │
                     └────────┬────────┘
                              ↓
                     ┌─────────────────┐
                     │    Connector    │
                     └────────┬────────┘
                              ↓
                     ┌─────────────────┐
                     │ Job Ingestion   │
                     └────────┬────────┘
                              ↓
                     ┌─────────────────┐
                     │     Job DB      │
                     └────────┬────────┘
                              ↓
                     ┌─────────────────┐
                     │ Deduplication   │
                     │     Engine      │
                     └────────┬────────┘
                              ↓
                    ┌─────────┴─────────┐
                    ▼                   ▼
             Canonical Job       Duplicate Link
```

> **Roadmap Note**: Phase 4 establishes deterministic cross-source job deduplication, canonical job linking, and false-positive prevention. User profiles, candidate matching, AI/LLMs, notifications, and dashboard UIs remain strictly scoped to Phases 5+.

---

## 3. End-to-End System Workflow (Roadmap Context)

The end-to-end platform workflow spans from career portal discovery to user alerts:

```text
       +-----------------------------------------------+
       |           Target Career Portals               |
       |  (Greenhouse, Lever, Workday, Custom APIs)    |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |             Job Connectors                    |
       |    (Phase 2: Standardized Ingestion - ACTIVE) |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |            Monitoring Engine                  |
       |        (Phase 3: Scheduled Dispatch - ACTIVE) |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |          Deduplication & Storage              |
       |   (Phase 4: Identity & Canonicalization-ACTIVE)|
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |       Database (PostgreSQL + Repositories)    |
       |        (Phase 1: Persistence Layer - ACTIVE)  |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |      User Profiles & Authentication           |
       |    (Phase 5: Candidate Experience - ACTIVE)   |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |             Matching Engine                   |
       |     (Phase 6: User Profile & Skill Scoring)   |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |          Notification Dispatcher              |
       |    (Phase 8: Email, SMS, Webhooks, Push)      |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |               User Dashboard                  |
       |    (Phase 9: React/TypeScript Web Client)     |
       +-----------------------------------------------+
```

---

## 3. Backend Architecture & Layers

The backend follows a layered architecture with strict separation of concerns:

```text
backend/
├── alembic/        # Schema migrations & database versioning
├── app/
│   ├── api/        # HTTP Routers & Controllers (FastAPI)
│   ├── core/       # Configuration, engine, connection pool, sessionmaker
│   ├── models/     # Declarative SQLAlchemy 2.x Entities (Company, CareerSource, Job)
│   ├── schemas/    # Request/Response Validation DTOs (Pydantic v2)
│   ├── services/   # Domain Business Logic & Workflow Orchestration (Phase 2+)
│   ├── repositories/ # Data Access Repositories (Company, CareerSource, Job)
│   ├── workers/    # Background Job Execution & Schedulers (Phase 3)
│   ├── connectors/ # External Career Portal Integrations (Phase 2)
│   ├── ai/         # LLM Orchestration & Embeddings (Phase 7+)
│   ├── notifications/ # Alert Delivery Channels (Phase 8)
│   └── main.py     # Application Entrypoint & Middleware Assembly
└── tests/          # Pytest Test Suite
```

### Layer Responsibilities & Strict Boundaries

| Module | Core Responsibility | Prohibited Dependencies |
| :--- | :--- | :--- |
| `api/` | Route handling, HTTP status codes, request parsing | Direct database queries, business calculations |
| `core/` | Configuration, database engine, pooling, sessionmaker | Direct route definitions, domain entities |
| `models/` | Relational schema definitions (SQLAlchemy 2.x) | HTTP schemas, external API clients |
| `schemas/` | Serialization, schema validation, DTOs | Database sessions, SQL queries |
| `services/` | Business rules, domain workflows | Direct HTTP response formatting |
| `repositories/`| CRUD operations, query optimization | HTTP concepts, direct presentation logic |
| `workers/` | Task queue consumers, scheduled jobs | HTTP request contexts |
| `connectors/` | Scraping, external API communication | Notification logic, persistence directly |
| `ai/` | Prompt engineering, model inference, embeddings | Routing, database transaction commits |
| `notifications/` | SMTP, SMS, webhook message delivery | Job monitoring business rules |

---

## 4. Frontend Architecture

The frontend is structured as a single-page application using React, TypeScript, and Vite:

```text
frontend/src/
├── components/     # Reusable UI widgets and atomic components
├── pages/          # Top-level route pages (Dashboard, Jobs, Settings)
├── layouts/        # Page wrappers (Sidebar, Top Navigation, Shell)
├── hooks/          # Custom reusable React hooks
├── services/       # Typed HTTP client modules calling backend APIs
├── stores/         # Client-side state stores
├── types/          # Shared TypeScript interfaces & DTOs
├── App.tsx         # Root component shell
├── main.tsx        # React DOM mount entrypoint
└── index.css       # Design tokens and global CSS
```

---

## 5. Architectural Decisions (ADR Summary)

1. **Monorepo Layout**: Backend (`Python/FastAPI`) and Frontend (`React/TypeScript/Vite`) reside in a unified repository with shared documentation and docker orchestration.
2. **Configuration via Pydantic Settings**: Eliminates ad-hoc `os.environ` lookups, validates environment variables at startup, and provides IDE autocompletion.
3. **Phase 1 Persistence Strategy**: PostgreSQL as standard database, modern SQLAlchemy 2.x `DeclarativeBase` with timezone-aware UTC timestamps, UUID primary keys (`app.models.base.GUID`), and Alembic migrations.
4. **Repository Pattern**: All database interactions are encapsulated behind repositories (`CompanyRepository`, `CareerSourceRepository`, `JobRepository`), strictly preventing HTTP handlers or future scrapers from writing raw queries.
5. **Two-Tier Health Probes**:
   - `GET /health` (`GET /api/v1/health`): Process liveness probe.
   - `GET /api/v1/health/db`: Database connectivity readiness probe running lightweight `SELECT 1`.
6. **Phase 6 Deterministic Matching**: Pure, database-independent matching engine operating on extracted features across 8 dimensions with dynamic normalization for missing data and full explainability.

---

## 6. Matching Engine Architecture (Phase 6)

```text
                  CandidateProfile
                        │
                        ▼
                 CandidateFeatures
                        │
                        ▼
                  MatchingEngine  ◄── JobFeatures ◄── Job + JobRequirements
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
    Component Scores             Explanations
          │                           │
          └─────────────┬─────────────┘
                        ▼
             Normalized Weighted Score
                        │
                        ▼
                   MatchResult
                        │
                        ▼
                JobMatch (Persisted)
```

- **Pure Engine**: `MatchingEngine` has zero database dependencies, enabling isolated unit testing and high performance batch evaluation.
- **Dynamic Missing Data Strategy**: Missing job attributes (e.g. undisclosed salary or education) yield `UNKNOWN` or `NOT_APPLICABLE` and are dynamically removed from the denominator rather than penalizing candidate scores.
- **Deterministic Explanations**: Every reason template traces directly to evaluated dimension outcomes without AI hallucination.

---

## 7. AI Intelligence & Semantic Matching Architecture (Phase 7)

Phase 7 introduces structured LLM extraction, vector embeddings via `pgvector`, semantic cosine similarity, and hybrid scoring while strictly preserving Phase 6 deterministic matching as the authoritative baseline:

```text
                    JOB
                     │
                     ▼
             Job Description
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   Deterministic           AI Extraction
   Job Features            & Normalization
          │                     │
          │              ┌──────┴──────┐
          │              ▼             ▼
          │          Structured     Embeddings
          │          Requirements      │
          │              │             │
          └──────────────┼─────────────┘
                         ▼
                 AI Matching Layer
                         │
                         ▼
                 Enhanced MatchResult
                         │
                         ▼
              Candidate / Dashboard
```

- **Authoritative Deterministic Baseline**: The Phase 6 engine always calculates the baseline score first. Even during AI provider outages, timeouts, or rate limits, the system seamlessly produces valid match results.
- **Provider Abstraction**: Decoupled behind `LLMProvider` and `EmbeddingProvider`, with production `OpenAIProvider` and zero-network `FakeProvider` for fast, offline CI testing.
- **pgvector Vector Storage**: Native 1536-dimensional float vectors stored directly in PostgreSQL with SHA-256 content-hash cache validation.
- **Hybrid Score Synthesis**: Formula $0.70 \times \text{Deterministic} + 0.30 \times \text{Semantic}$ with hard constraint safety guardrails that cap the hybrid score if critical dimensions (e.g., workplace type or required skills) are hard mismatches.
- **Score-Immutable AI Explanations**: Narrative summaries, strengths, gaps, and recommendations are generated from structured facts; the LLM cannot alter the calculated match score.

---

## 7. Notification & Alerting Architecture (Phase 8 Active)

```text
               Deterministic / Hybrid Match Result
                                │
                                ▼
                       Notification Event
                                │
                                ▼
                     NotificationService
              (Preference & Threshold Evaluation)
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       Hourly Rate Limiter             Idempotency Deduplicator
       (Cap: max_per_hour)            (SHA-256 Canonical Job Key)
                │                               │
                └───────────────┬───────────────┘
                                ▼
                           Notification
                     (Record Status: PENDING)
                                │
                                ▼
                       NotificationDelivery
                   (Channel Attempts: PENDING)
                                │
                                ▼
                    NotificationDeliveryWorker
                   (Atomic Claim & Backoff Queue)
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
            EmailChannel                 WebhookChannel
                 │                             │
           EmailProvider                 WebhookProvider
       (SMTP / Fake Provider)       (HTTP POST / SSRF Guarded)
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                     Delivery Status Recorded
             (SENT / RETRYING / FAILED / CANCELLED)
```

- **Downstream Consumer**: Notifications are decoupled from ingestion and matching. A failure in notification delivery never impedes job ingestion or matching persistence.
- **Provider-Independent Abstractions**: `EmailProvider` and `WebhookProvider` isolate protocol details from business alerting rules.
- **Multi-Tenant Isolation**: Candidate notifications and preferences are strictly isolated via user authentication tokens.
- **Idempotency & Flood Protection**: SHA-256 idempotency keying bound to canonical job identities prevents duplicate alerts from repeat monitoring runs or portal reposts. Hourly caps protect candidates from alert spam.
- **Atomic Claims & Stale Recovery**: Safe PostgreSQL concurrency prevents race conditions across multi-worker environments, recovering hung executions automatically.
