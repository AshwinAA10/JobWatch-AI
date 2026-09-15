# JobWatch AI — Architecture Specification

## 1. System Vision

JobWatch AI is an intelligent opportunity-monitoring platform designed to eliminate the friction of searching for careers across dispersed company career portals.

By connecting directly to target company portals, normalizing disparate job postings, running semantic similarity matching against user career profiles, and alerting users in real time, JobWatch AI ensures professionals never miss high-value opportunities.

---

## 2. High-Level System Architecture

The end-to-end platform workflow spans from career portal discovery to user alerts:

```text
       +-----------------------------------------------+
       |           Target Career Portals               |
       |  (Greenhouse, Lever, Workday, Custom APIs)     |
       +-----------------------------------------------+
                               |
                               v
       +-----------------------------------------------+
       |             Job Connectors                    |
       |       (Phase 2: Standardized Ingestion)       |
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
       |      (Phase 1: Persistence & Data Access)     |
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
backend/app/
├── api/            # HTTP Routers & Controllers (FastAPI)
├── core/           # Configuration, Security, Environment (Pydantic Settings)
├── models/         # Database ORM Entities (Phase 1: SQLAlchemy)
├── schemas/        # Request/Response Validation DTOs (Pydantic)
├── services/       # Domain Business Logic & Workflow Orchestration
├── repositories/   # Data Access Layer & Query Abstraction (Phase 1)
├── workers/        # Asynchronous Job Execution & Schedulers (Phase 3)
├── connectors/     # External Career Portal Integrations (Phase 2)
├── ai/             # LLM Orchestration & Embeddings (Phase 7+)
├── notifications/  # Alert Delivery Channels (Phase 8)
└── main.py         # Application Entrypoint & Middleware Assembly
```

### Layer Responsibilities & Strict Boundaries

| Module | Core Responsibility | Prohibited Dependencies |
| :--- | :--- | :--- |
| `api/` | Route handling, HTTP status codes, request parsing | Direct database queries, business calculations |
| `core/` | Configuration, logging, global singletons | Direct route definitions, domain models |
| `models/` | Relational schema definitions (Phase 1) | HTTP schemas, external API clients |
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

### Responsibilities

- **`services/`**: All network interaction with the backend is isolated in `services/`. Components never make raw `fetch` calls directly.
- **`types/`**: Interfaces mirror the backend Pydantic schemas, ensuring end-to-end type safety.
- **`components/` vs `pages/`**: Reusable widgets live in `components/`, while route-level views live in `pages/`.

---

## 5. Architectural Decisions (ADR Summary)

1. **Monorepo Layout**: Backend (`Python/FastAPI`) and Frontend (`React/TypeScript/Vite`) reside in a unified repository with shared documentation and docker orchestration, simplifying versioning and cross-stack coordination.
2. **Configuration via Pydantic Settings**: Eliminates ad-hoc `os.environ` lookups, validates environment variables at startup, and provides IDE autocompletion.
3. **Phase Isolation**: Only components required for Phase 0 are operational. Future components exist strictly as package boundaries to prevent premature overengineering.
4. **Health Endpoint Standard**: Both `/health` and `/api/v1/health` are exposed for container orchestrators (Kubernetes/ECS) and API consumers.
