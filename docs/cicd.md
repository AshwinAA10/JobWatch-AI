# JobWatch AI — CI/CD Pipeline Documentation

## 1. Overview
JobWatch AI employs an automated GitHub Actions continuous integration and continuous deployment strategy designed to enforce quality, security, and schema safety before any code touches staging or production.

---

## 2. Pipeline Workflows

### Continuous Integration (`.github/workflows/ci.yml`)
Triggered on every pull request and push to the `main` branch:
1. **Backend Checks**:
   - Boots a PostgreSQL + `pgvector` ephemeral service container.
   - Runs full dependency installations (`pip install -r backend/requirements.txt`).
   - Executes pending database migrations (`alembic upgrade head`) and verifies schema alignment (`alembic check`).
   - Runs complete test suite (`pytest backend/tests -v`).
   - Executes `scripts/validate_production_config.py` to confirm configuration consistency.
2. **Frontend Checks**:
   - Installs frozen dependencies (`npm ci`).
   - Runs Vitest component unit and integration test suite (`npm test -- --run`).
   - Compiles TypeScript and builds production bundles (`npm run build`).
3. **Docker Validation**:
   - Validates multi-service topology syntax (`docker compose config`).
   - Performs test builds of `backend/Dockerfile` and `frontend/Dockerfile`.

### Continuous Deployment (`.github/workflows/deploy.yml`)
Triggered automatically on merge to `main` or manually via `workflow_dispatch`:
1. **Quality Gate Requirement**: Depends on successful execution of `ci.yml`.
2. **Environment Protection**: Restricted to authorized production environments with branch protections.
3. **Smoke Test Verification**: Executes `scripts/smoke_test.py` against live readiness probes.

---

## 3. Secret Management & GitHub Secrets

The following secrets must be configured in GitHub Repository Settings:
- `PRODUCTION_API_URL`: Root URL of deployed FastAPI backend.
- `BACKEND_DEPLOY_HOOK_URL`: Webhook URL for managed container hosting platform.
- `FRONTEND_DEPLOY_HOOK_URL`: Webhook URL for static CDN hosting platform.
- `DATABASE_URL`: Production connection string (for manual migration workflows).

---

## 4. Release Tagging & Promotion

- Image artifacts are tagged using immutable Git Commit SHAs (`jobwatch-api:${{ github.sha }}`) to guarantee unambiguous rollback targets.
- Release versioning is synchronized with `APP_VERSION` in `app/core/config.py`.
