# JobWatch AI — Production Readiness & Release Checklist

This checklist must be reviewed and signed off prior to deploying new versions of JobWatch AI to production.

---

## 1. Pre-Deployment Verification

- [ ] **Continuous Integration**:
  - [ ] GitHub Actions CI pipeline is passing (`ci.yml`).
  - [ ] All backend unit and integration tests passing (`pytest backend/tests`).
  - [ ] All frontend unit tests passing (`npm test`).
  - [ ] Frontend builds with 0 TypeScript and bundling errors (`npm run build`).
- [ ] **Schema & Database**:
  - [ ] Database migrations reviewed and verified non-destructive.
  - [ ] `alembic check` passes with 0 drift.
  - [ ] Pre-deployment database snapshot or backup verified.
- [ ] **Configuration & Secrets**:
  - [ ] `APP_ENV=production` set.
  - [ ] `DEBUG=false` verified.
  - [ ] Strong random `JWT_SECRET` configured (>= 32 chars).
  - [ ] `CORS_ORIGINS` explicitly limited to production domains (no wildcard `*`).
  - [ ] OpenAI API key and timeouts configured.
  - [ ] Run `python scripts/validate_production_config.py` with zero errors.

---

## 2. Deployment Execution

- [ ] **Step 1: Database Migration**:
  - [ ] Execute `alembic upgrade head` from deployment runner or bastion.
- [ ] **Step 2: Backend API Deployment**:
  - [ ] Deploy new backend container image.
  - [ ] Verify `GET /health/live` returns HTTP 200.
  - [ ] Verify `GET /health/ready` returns HTTP 200 (`database: connected`).
- [ ] **Step 3: Background Worker Deployment**:
  - [ ] Restart worker service with updated container image.
  - [ ] Inspect worker logs to confirm scheduler initialization and 0 restart loops.
- [ ] **Step 4: Frontend Web Deployment**:
  - [ ] Deploy static assets to CDN.
  - [ ] Verify frontend loads in browser with HTTPS.

---

## 3. Post-Deployment Verification (Smoke Tests)

- [ ] Run automated smoke test: `python scripts/smoke_test.py --target-url https://api.jobwatch.ai`.
- [ ] Log in as a test candidate and verify JWT token issuance.
- [ ] Load dashboard: verify metrics, match scores, and application tracking tabs render.
- [ ] Verify telemetry at `/api/v1/metrics` reflects incoming requests without errors.
- [ ] Verify application logs show structured output with `request_id` and masked credentials.

---

## 4. Rollback Signoff (If Issues Encountered)

- [ ] Revert backend and worker services to previous commit SHA image tag.
- [ ] Revert CDN frontend deployment to prior release.
- [ ] Confirm service health recovers on previous release.
- [ ] Document cause in incident log.
