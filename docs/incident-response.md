# JobWatch AI — Incident Response & Disaster Recovery

## 1. Severity Levels

| Severity | Definition | Target Response | Target Resolution |
|---|---|---|---|
| **SEV-1 (Critical)** | Core API unavailable, database down, or widespread data corruption. | < 15 minutes | < 2 hours |
| **SEV-2 (Major)** | Connector monitoring halted, notification failure, or AI degradation. | < 1 hour | < 6 hours |
| **SEV-3 (Minor)** | Non-blocking UI defect or non-critical background task delay. | < 4 hours | Next release |

---

## 2. Immediate Incident Protocols

### Scenario A: Total API Outage (5xx Spike / Process Crash)
1. **Triage**:
   - Check `GET /health/live` to determine if process is alive.
   - Check `GET /health/ready` to verify PostgreSQL connectivity.
   - Inspect container logs for unhandled exceptions or memory limit (OOM) kills.
2. **Containment**:
   - If caused by bad release: Trigger immediate rollback to previous image tag.
   - If caused by database lock: Terminate long-running queries or restart database instance.
3. **Verification**:
   - Run `python scripts/smoke_test.py --target-url <PROD_URL>`.

---

### Scenario B: Database Unreachable or Severed
1. **Diagnosis**:
   - `GET /health/ready` returns HTTP 503 `{"database": "disconnected"}`.
2. **Action**:
   - Verify cloud provider status for PostgreSQL instance.
   - Check connection counts against `DB_MAX_OVERFLOW` and provider limits.
   - If database filesystem or data is corrupted, initiate Point-In-Time Recovery (PITR) from latest automated backup.

---

### Scenario C: Secret Compromise
1. **JWT Secret Leak**:
   - Immediately rotate `JWT_SECRET` in production secrets manager and restart API services.
   - Note: This will invalidate all active candidate sessions, requiring re-login (defensive posture).
2. **OpenAI or SMTP Key Leak**:
   - Revoke compromised API key in provider console.
   - Generate replacement key and update production environment variables.

---

## 3. Post-Incident Review (PIR)
For every SEV-1 and SEV-2 incident:
1. Conduct post-mortem within 48 hours.
2. Document timeline of events, root cause, impact duration, and remediation.
3. Track action items to prevent recurrence.
