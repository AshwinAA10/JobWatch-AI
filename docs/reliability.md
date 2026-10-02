# JobWatch AI — Reliability Architecture & Resilience Framework

## Overview
Phase 11 hardens JobWatch AI so that individual component outages (third-party career APIs, AI models, email providers, network interruptions) are completely isolated and never cause catastrophic failure of the entire system.

---

## 1. Database Connection Resilience

- **Connection Pool Configuration**:
  - `pool_pre_ping=True`: Probes connections before giving them to transactions, discarding stale or severed sockets.
  - `connect_timeout=10`: Avoids thread hangs when connecting to unreachable database instances.
  - `pool_size=5`, `max_overflow=10`, `pool_recycle=1800`: Recycles long-lived connections periodically.
- **Transaction Rollback Protection**:
  - `get_db` FastAPI session dependency guarantees that if an unhandled error occurs during request execution, the session is cleanly rolled back and closed.

---

## 2. Ingestion & Connector Resilience

- **Failure Isolation**: Each job source sync is isolated. A failure in Greenhouse or Lever does not abort the monitoring loop or corrupt other source pipelines.
- **Bounded Retries with Exponential Backoff**: Transient HTTP 429 and 5xx errors trigger bounded retries with jitter and Retry-After header compliance.

---

## 3. AI Service Resilience & Graceful Degradation

- **Deterministic Fallback**: If OpenAI is unavailable, timed out, or ratelimited, matching degrades gracefully to deterministic rule-based matching.
- **Timeouts**: Every external AI request enforces a strict timeout (`OPENAI_TIMEOUT=30.0s`).
- **Response Validation**: All LLM structured outputs are validated against Pydantic schemas before ingestion or persistence.

---

## 4. Notification Subsystem Resilience

- **Dead-Letter State Tracking**: Unsuccessful deliveries are marked with failure status and retry counts, preventing infinite loops.
- **Idempotency**: Notification events use unique combinations of candidate, job, and channel to prevent duplicate messages.

---

## 5. Graceful Process Shutdown

- Handles `SIGTERM` and `SIGINT` cleanly via FastAPI's `lifespan` manager:
  1. Stops background monitoring schedulers.
  2. Waits for safe completion of active jobs.
  3. Closes HTTP client sessions.
  4. Disposes SQLAlchemy engine pool (`engine.dispose()`).
