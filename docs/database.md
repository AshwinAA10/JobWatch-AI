# JobWatch AI — Database Specification & Architecture

## 1. Architecture Overview

JobWatch AI persistence is built on **PostgreSQL** using modern **SQLAlchemy 2.x ORM**, **Alembic** schema migrations, and the **Repository Pattern** for data access abstraction.

```text
┌─────────────────────────┐
│       FastAPI API       │
│  (HTTP / Controllers)   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Domain Services     │
│     (Business Logic)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       Repositories      │
│  (Data Access Layer)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   SQLAlchemy 2.x ORM    │
│  (DeclarativeBase / DB) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   PostgreSQL Database   │
└─────────────────────────┘
```

---

## 2. Core Entities & Relationships

```mermaid
erDiagram
    Company ||--o{ CareerSource : "has (1:N)"
    Company ||--o{ Job : "employs (1:N)"
    CareerSource ||--o{ Job : "publishes (1:N)"
    CareerSource ||--o{ MonitoringRun : "records (1:N)"
    Job ||--o| Job : "canonical_for (self 1:N)"
    Job ||--o{ JobDuplicate : "canonical_record (1:N)"
    Job ||--o{ JobDuplicate : "duplicate_record (1:N)"

    Company {
        UUID id PK
        string name "required"
        string slug UK "unique, indexed"
        string website_url "nullable"
        text description "nullable"
        boolean is_active "indexed, default true"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    CareerSource {
        UUID id PK
        UUID company_id FK "CASCADE"
        string name "required"
        string source_type "indexed (greenhouse, lever, workday)"
        string base_url "required"
        boolean is_active "indexed, default true"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    MonitoringRun {
        UUID id PK
        UUID career_source_id FK "CASCADE"
        string status "indexed (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"
        timestamptz started_at "nullable, indexed"
        timestamptz completed_at "nullable"
        int jobs_found "default 0"
        int jobs_inserted "default 0"
        int jobs_updated "default 0"
        int jobs_unchanged "default 0"
        text error_message "nullable"
        jsonb metadata "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    Job {
        UUID id PK
        UUID company_id FK "CASCADE"
        UUID career_source_id FK "CASCADE"
        UUID canonical_job_id FK "SET NULL, nullable, indexed"
        string external_id "nullable, indexed"
        string title "required"
        text description "nullable"
        string location "nullable"
        string employment_type "nullable"
        string workplace_type "nullable"
        string application_url "nullable"
        string source_url "nullable"
        timestamptz posted_at "nullable, indexed"
        timestamptz first_seen_at "indexed, default now"
        timestamptz last_seen_at "default now"
        boolean is_active "indexed, default true"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    JobDuplicate {
        UUID id PK
        UUID canonical_job_id FK "CASCADE, indexed"
        UUID duplicate_job_id FK "CASCADE, unique, indexed"
        string match_type "indexed (EXACT_EXTERNAL_ID, EXACT_APPLICATION_URL, EXACT_SOURCE_URL, EXACT_CANONICAL_KEY, HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, MANUAL)"
        float confidence_score "indexed"
        jsonb matched_fields "nullable"
        string reason "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    User ||--o| CandidateProfile : "owns (1:1)"
    CandidateProfile ||--o{ CandidateSkill : "possesses (1:N)"
    Skill ||--o{ CandidateSkill : "referenced_in (1:N)"
    CandidateProfile ||--o{ Experience : "has (1:N)"
    CandidateProfile ||--o{ Education : "has (1:N)"
    CandidateProfile ||--o| CandidatePreferences : "specifies (1:1)"
    CandidateProfile ||--o{ Resume : "uploads (1:N)"

    User {
        UUID id PK
        string email UK "unique, indexed"
        string password_hash "Argon2id"
        boolean is_active "indexed, default true"
        boolean is_verified "default false"
        timestamptz last_login_at "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    CandidateProfile {
        UUID id PK
        UUID user_id FK "CASCADE, unique, indexed"
        string first_name "nullable"
        string last_name "nullable"
        string headline "nullable"
        text bio "nullable"
        string phone "nullable"
        string city "nullable"
        string state "nullable"
        string country "nullable"
        float years_of_experience "nullable"
        string current_job_title "nullable"
        string current_company "nullable"
        string highest_education_level "nullable"
        string profile_visibility "default PRIVATE"
        int profile_completion_percent "default 0"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    Skill {
        UUID id PK
        string name "required"
        string normalized_name UK "unique, indexed"
        string category "nullable, indexed"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    CandidateSkill {
        UUID id PK
        UUID profile_id FK "CASCADE, indexed"
        UUID skill_id FK "CASCADE, indexed"
        string proficiency "BEGINNER, INTERMEDIATE, ADVANCED, EXPERT"
        float years_experience "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    Experience {
        UUID id PK
        UUID profile_id FK "CASCADE, indexed"
        string company_name "required"
        string job_title "required"
        text description "nullable"
        string location "nullable"
        string employment_type "nullable"
        date start_date "required"
        date end_date "nullable"
        boolean is_current "default false"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    Education {
        UUID id PK
        UUID profile_id FK "CASCADE, indexed"
        string institution_name "required"
        string degree "nullable"
        string field_of_study "nullable"
        string location "nullable"
        date start_date "nullable"
        date end_date "nullable"
        string grade "nullable"
        text description "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    CandidatePreferences {
        UUID id PK
        UUID profile_id FK "CASCADE, unique, indexed"
        json desired_titles "required"
        json preferred_locations "required"
        json workplace_types "required"
        json employment_types "required"
        int minimum_salary "nullable"
        int maximum_salary "nullable"
        string salary_currency "default USD"
        int minimum_experience_years "nullable"
        int maximum_experience_years "nullable"
        boolean willing_to_relocate "default false"
        string remote_preference "nullable"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }

    Resume {
        UUID id PK
        UUID profile_id FK "CASCADE, indexed"
        string filename "required"
        string content_type "required"
        string storage_key "required"
        int file_size "required"
        timestamptz uploaded_at "UTC"
        boolean is_active "default true"
        timestamptz created_at "UTC"
        timestamptz updated_at "UTC"
    }
```

### Constraints & Indexes
- **UUID Primary Keys**: Application-level RFC 4122 UUID primary keys (`app.models.base.GUID`) providing collision resistance and portability.
- **Foreign Keys**: Explicit relational integrity with `ON DELETE CASCADE` (`SET NULL` on `Job.canonical_job_id`).
- **Composite Unique Constraint**: `uq_jobs_source_external_id` enforces unique external job IDs per career source (`career_source_id`, `external_id`).
- **Self-Referential Canonical Constraint**: `ck_jobs_no_self_canonical` ensures `canonical_job_id != id`.
- **Duplicate Relationship Constraints**:
  - `ck_job_duplicates_no_self_duplicate` ensures `canonical_job_id != duplicate_job_id`.
  - `uq_job_duplicates_duplicate_job_id` enforces 1:1 duplicate-to-canonical mapping, guaranteeing a single canonical parent and preventing multiple parents or duplicate edge entries.
- **User & Candidate Constraints**:
  - `uq_users_email`: Enforces unique email per user.
  - `uq_candidate_profiles_user_id`: Enforces strictly one candidate profile per user (1:1).
  - `uq_skills_normalized_name`: Enforces unique canonical skills by normalized lowercase name.
  - `uq_candidate_skills_profile_skill`: Enforces composite uniqueness of `(profile_id, skill_id)`.
  - `uq_candidate_preferences_profile_id`: Enforces strictly one preferences record per profile.
  - `ck_experiences_valid_date_range`: Enforces `end_date IS NULL OR end_date >= start_date`.
  - `ck_educations_valid_date_range`: Enforces `start_date IS NULL OR end_date IS NULL OR end_date >= start_date`.
  - `ck_preferences_salary_range`: Enforces `minimum_salary IS NULL OR maximum_salary IS NULL OR maximum_salary >= minimum_salary`.
  - `ck_preferences_experience_range`: Enforces `minimum_experience_years IS NULL OR maximum_experience_years IS NULL OR maximum_experience_years >= minimum_experience_years`.
- **Composite Index**: `ix_jobs_company_active` optimizes frequent queries filtering active jobs for a company.
- **Deduplication Candidate Index**: `ix_jobs_dedup_candidates` on `(company_id, is_active, first_seen_at)` prevents $O(N^2)$ candidate queries during ingestion.

---

## 3. Timestamp & Timezone Strategy

All timestamp fields (`created_at`, `updated_at`, `posted_at`, `first_seen_at`, `last_seen_at`) are stored as **timezone-aware UTC** (`TIMESTAMP WITH TIME ZONE` / `DateTime(timezone=True)`).
- Application code ensures timestamps default to `datetime.now(timezone.utc)`.
- Server-side defaults use `func.now()` / `now()`.
- Machine-local time is never persisted into the database.

---

## 4. Connection Pooling Configuration

Connection pooling is configured centrally in `backend/app/core/database.py` via `create_db_engine()`:

| Parameter | Default | Purpose |
| :--- | :--- | :--- |
| `pool_size` | `5` | Steady-state connection pool capacity |
| `max_overflow` | `10` | Maximum surge connections permitted beyond pool size |
| `pool_timeout` | `30` | Seconds to wait before failing if all pool connections are busy |
| `pool_recycle` | `1800` | Recycles idle connections after 30 minutes to prevent stale timeouts |
| `pool_pre_ping` | `True` | Tests connection validity prior to checkout (detects drops instantly) |

---

## 5. Schema Migrations (Alembic)

Alembic manages versioned database migrations located under `backend/alembic/versions/`.

### Migration Commands

Run commands from the repository root:

```bash
# Upgrade database to latest migration
.venv\Scripts\python -m alembic -c backend/alembic.ini upgrade head

# Rollback one migration
.venv\Scripts\python -m alembic -c backend/alembic.ini downgrade -1

# Generate SQL migration DDL without applying (offline inspection)
.venv\Scripts\python -m alembic -c backend/alembic.ini upgrade head --sql
```

---

## 6. Local Database Startup

### Option A: Docker Compose (Recommended)
Start the PostgreSQL container:
```bash
docker compose up -d postgres
```

### Option B: Local PostgreSQL Service
Configure your local database credentials in `.env`:
```env
DATABASE_URL=postgresql+psycopg://your_user:your_password@localhost:5432/jobwatch
```

---

## 7. Database Readiness Verification

The database readiness probe endpoint is accessible at:
```text
GET /api/v1/health/db
```

Sample successful response (`200 OK`):
```json
{
  "status": "healthy",
  "database": "connected",
  "latency_ms": 1.45,
  "timestamp": "2026-09-17T16:00:00.000Z"
}
```

If the database is unreachable, the endpoint returns `503 Service Unavailable` with clean diagnostic details without exposing database credentials or stack traces.
