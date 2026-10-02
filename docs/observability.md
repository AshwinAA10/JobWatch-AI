# JobWatch AI — Observability & Telemetry Architecture

## Overview
Phase 11 introduces comprehensive observability into JobWatch AI without requiring heavy third-party SaaS agents or violating data privacy.

---

## 1. Request Correlation & Context Propagation

Every HTTP request passing through JobWatch AI is tracked with an `X-Request-ID`:
- **Preservation**: If an inbound client or load balancer provides `X-Request-ID`, it is preserved (up to 64 characters).
- **Generation**: If absent, a random UUIDv4 is minted.
- **Context Binding**: The ID is stored in Python's `contextvars` via `request_id_ctx` in `app.core.logging`.
- **Response Propagation**: Returned to callers in the `X-Request-ID` HTTP response header.

---

## 2. Structured Logging & Redaction

### Formatter
Logs are formatted with timestamp, level, logger module, and `request_id` (when present in the current async context).

### Sensitive Data Masking (`SensitiveDataFilter`)
The following patterns are automatically redacted before stream output:
- **Bearer Tokens / JWTs**: `Bearer eyJ...` → `Bearer [REDACTED_TOKEN]`
- **Passwords**: `password="..."` → `password="[REDACTED_PASSWORD]"`
- **Secrets / Keys**: `secret="..."` → `secret="[REDACTED_SECRET]"`
- **Database Connection Strings**: `postgresql+psycopg://user:pass@host/db` → credentials masked with `[REDACTED_DB_PASS]`

---

## 3. Health & Readiness Probes

### Endpoints
1. `GET /health` and `GET /health/live`:
   - Answers: *Is the process alive?*
   - Verifies process execution; does not fail if downstream database is temporarily degraded.
2. `GET /health/ready` and `GET /health/db`:
   - Answers: *Can this instance safely serve user traffic?*
   - Probes PostgreSQL with a lightweight `SELECT 1` query.
   - On connection failure, returns `HTTP 503 Service Unavailable` with latency details and generic error messages (no credentials or stack traces).

---

## 4. In-Memory Telemetry Metrics

Metrics are exposed via `GET /api/v1/metrics`:
- **HTTP Request Metrics**: Count, errors, and average latency per generalized endpoint template (e.g., `/api/v1/jobs/{id}`).
- **Cardinality Protection**: Dynamic entity IDs (UUIDs and numeric keys) are collapsed into path templates to prevent unbounded memory growth.
- **Subsystem Metrics**: Connector sync attempts/failures, AI requests/failures, notification delivery attempts/failures.
