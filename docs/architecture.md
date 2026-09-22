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

> **Roadmap Note**: Phase 3 automates periodic execution, provides development trigger APIs, and records `MonitoringRun` metrics. Semantic deduplication, candidate matching, notifications, and dashboard UIs remain strictly scoped to Phases 4+.

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
       |        (Phase 3: Scheduled Dispatch)          |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |          Deduplication & Storage              |
       |       (Phase 4: Hashing & Canonicalization)   |
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
       |             AI Intelligence                   |
       |       (Phase 7: Embeddings & Extraction)      |
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
