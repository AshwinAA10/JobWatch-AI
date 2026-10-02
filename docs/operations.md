# JobWatch AI — Operations Runbook & Recovery Guide

## Overview
This runbook provides actionable procedures for production operational issues, disaster recovery, and PostgreSQL maintenance.

---

## 1. PostgreSQL Backup & Restore Strategy

### Automated Backup Recommendation
Take daily physical or logical backups using `pg_dump`:
```bash
# Logical backup command
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -b -v -f /backups/jobwatch_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Procedure
```bash
# 1. Stop backend application to avoid write conflicts
# 2. Restore database:
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME -v -c /backups/jobwatch_backup.dump
# 3. Verify database health:
curl -s http://localhost:8000/health/ready
```

---

## 2. Troubleshooting & Recovery Procedures

### Symptom: Application Won't Start
- **Check**: Inspect stderr for `Production configuration validation failed`.
- **Cause**: Unsafe defaults in production (`DEBUG=true`, default `JWT_SECRET`, or wildcard CORS).
- **Recovery**: Update environment variables with strong random secrets and explicit production origins.

### Symptom: `GET /health/ready` returns HTTP 503
- **Check**: Test connection string and network route to PostgreSQL container/host.
- **Cause**: Database instance stopped, network partition, or connection limit exhausted.
- **Recovery**: Restart PostgreSQL container, check DB connection limits, and verify credentials.

### Symptom: High Rate of 429 Responses on Auth
- **Check**: Check `GET /api/v1/metrics` for request counts by endpoint.
- **Cause**: Potential credential stuffing or brute-force attack from a specific IP.
- **Recovery**: Verify offending IP address. Rate limiter automatically cools down within 60 seconds.

### Symptom: OpenAI Outage / Rate Limit
- **Check**: Inspect metrics `ai.failures`.
- **Behavior**: System automatically degrades gracefully; deterministic matching engine continues to score jobs without stalling user requests.

---

## 3. Operational Procedures

### Deploying a New Release
1. Verify CI is green on GitHub Actions.
2. Trigger deployment workflow or platform deploy hook.
3. Run smoke tests:
   ```bash
   python scripts/smoke_test.py --target-url https://api.jobwatch.ai
   ```

### Running Production Migrations
```bash
# Execute forward migrations against production DB
alembic upgrade head

# Confirm zero drift
alembic check
```

### Viewing Logs & Traces
- Filter logs by `request_id` to correlate an entire user interaction.
- Application logs automatically mask passwords, bearer tokens, and DB connection strings.

### Managing Background Workers
- The background worker runs as a dedicated process: `python -m app.worker`.
- To restart: send `SIGTERM` to the container; it will complete active notification batches and terminate cleanly within 15 seconds.

---

## 4. Proposed Initial Operational Targets (SLOs)

- **API Availability**: ≥ 99.9% uptime for core API endpoints.
- **API Latency**: p95 < 250ms for job queries, p95 < 150ms for application CRUD.
- **Ingestion Success**: ≥ 99.0% of scheduled connector jobs completed.
- **Notification Delivery**: ≥ 99.5% delivery success within 5 minutes of job ingestion.
