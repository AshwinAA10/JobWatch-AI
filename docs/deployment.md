# JobWatch AI — Production Deployment Guide

## 1. Production Architecture Overview

The JobWatch AI production architecture decouples user-facing web services from long-running background tasks while maintaining atomic database persistence:

```text
                             Internet
                                │
                        HTTPS / DNS / TLS
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
     ┌─────────────────────┐         ┌─────────────────────┐
     │  Frontend Web App   │         │    API Gateway      │
     │  React + Vite SPA   │         │  (Reverse Proxy)    │
     │   (Static CDN)      │         └──────────┬──────────┘
     └─────────────────────┘                    │
                                                ▼
                                     ┌─────────────────────┐
                                     │   FastAPI Backend   │
                                     │  (Uvicorn Workers)  │
                                     └──────────┬──────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │                              │                              │
                 ▼                              ▼                              ▼
      ┌─────────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
      │     PostgreSQL      │        │  Background Worker  │        │  External Services  │
      │  + pgvector (DB)    │        │  (Scheduler/Sync)   │        │ (OpenAI, SMTP, etc) │
      └─────────────────────┘        └─────────────────────┘        └─────────────────────┘
```

---

## 2. Platform Decisions & Service Topology

1. **Frontend Hosting**:
   - Built statically via `npm run build`.
   - Served via static CDN hosting (e.g. Vercel, Netlify, or Dockerized Nginx).
   - Environment: `VITE_API_BASE_URL` baked at compile-time to point to backend API domain (e.g. `https://api.jobwatch.ai/api/v1`).

2. **Backend API**:
   - Containerized FastAPI application using non-privileged system user (`jobwatch`).
   - Managed container service (e.g. Render Web Service, Railway, Fly.io, or AWS ECS).
   - Scaled independently from background workers.

3. **Background Worker**:
   - Runs `python -m app.worker` in a dedicated container.
   - Executes periodic monitoring cycles (`MONITORING_INTERVAL_SECONDS=900`) and notification dispatches without tying up HTTP request threads.
   - Scaled conservatively (1 instance) to eliminate distributed scheduling race conditions.

4. **PostgreSQL**:
   - Managed PostgreSQL 16+ instance with `pgvector` extension enabled.
   - Enforces TLS encryption (`sslmode=require`), daily automated physical snapshots, and restricted network access.

---

## 3. Production Environment Variables Reference

| Category | Variable Name | Required | Default / Example | Notes |
|---|---|---|---|---|
| **App** | `APP_NAME` | No | `JobWatch AI` | System identifier |
| | `APP_ENV` | Yes | `production` | Triggers strict startup validation |
| | `DEBUG` | Yes | `false` | Must be `false` in production |
| | `BACKEND_PORT` | No | `8000` | Port listened by ASGI server |
| **Security** | `JWT_SECRET` | Yes | *Secure 32+ char secret* | Startup rejects dev secrets |
| | `JWT_ALGORITHM` | No | `HS256` | Token signing algorithm |
| | `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Token lifetime |
| | `CORS_ORIGINS` | Yes | `https://app.jobwatch.ai` | Comma-separated allowed origins |
| **Database** | `DATABASE_URL` | Yes | `postgresql+psycopg://...` | Connection string with SSL |
| | `DB_POOL_SIZE` | No | `5` | SQLAlchemy pool size |
| | `DB_MAX_OVERFLOW` | No | `10` | SQLAlchemy overflow limit |
| | `DB_CONNECT_TIMEOUT`| No | `10` | Fail fast on connection loss |
| **AI** | `OPENAI_API_KEY` | Optional | `sk-...` | Enables semantic parsing |
| | `OPENAI_MODEL` | No | `gpt-4o-mini` | Extraction LLM model |
| **Notifications**| `NOTIFICATIONS_ENABLED` | No | `true` | Subsystem master switch |
| | `EMAIL_NOTIFICATIONS_ENABLED`| No | `false` | Enable SMTP delivery |
| | `SMTP_HOST` | Cond. | `smtp.provider.com` | Required if email enabled |
| | `SMTP_PORT` | Cond. | `587` | Standard submission port |
| | `SMTP_USERNAME` | Cond. | *Provider username* | |
| | `SMTP_PASSWORD` | Cond. | *Provider password* | Injected via secret |

---

## 4. Database Migration Procedure

Database migrations are **never** executed implicitly during container boots.

### Deployment Workflow:
1. **Build Step**: CI tests pass and container image is built.
2. **Pre-Deployment Migration**:
   ```bash
   alembic upgrade head
   alembic check
   ```
3. **Application Deployment**: Shift traffic to new backend containers.
4. **Post-Deployment Smoke Test**: Execute `scripts/smoke_test.py` to confirm connectivity.

---

## 5. Rollback Strategy

If a newly deployed release fails healthchecks or smoke verification:
1. **Application Rollback**:
   - Revert traffic to the previous container image tag (e.g. `jobwatch-api:<previous-commit-sha>`).
   - Trigger static frontend rollback in CDN dashboard.
2. **Database Rollback Policy**:
   - Forward migrations are designed to be non-breaking (additive schema design).
   - Only execute `alembic downgrade` if strictly necessary and after verifying that user data will not be destroyed.
   - For severe corruption, initiate Point-In-Time Recovery (PITR) from the automated pre-deployment snapshot.
