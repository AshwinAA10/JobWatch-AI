# JobWatch AI — Development Guide

This guide provides instructions for setting up, running, testing, and validating JobWatch AI during **Phase 1: Database + Backend Foundation**.

---

## 1. Prerequisites

Ensure you have the following installed on your local system:

- **Python**: 3.11+ (Python 3.13 tested)
- **Node.js**: 20.x+
- **npm**: 10.x+
- **Git**: 2.40+
- **Docker & Docker Compose** (recommended for PostgreSQL container)
- **PostgreSQL**: 15+ (if running natively instead of Docker)

---

## 2. Quick Setup

### Step A: Environment Configuration

Copy the example environment configuration into `.env`:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Review the values in `.env`. By default:
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:5173`
- PostgreSQL is configured for `postgresql+psycopg://jobwatch:jobwatch_dev@localhost:5432/jobwatch`

---

## 3. Database Setup

### Option 1: Using Docker Compose (Recommended)

Start the PostgreSQL service in the background:

```bash
docker compose up -d postgres
```

### Option 2: Using Local PostgreSQL Service

If you have a local PostgreSQL installation, ensure a database named `jobwatch` exists and update `DATABASE_URL` in `.env`.

### Run Alembic Migrations

Apply database schema migrations to bring the database schema up to date:

```bash
# Windows
.venv\Scripts\python -m alembic -c backend/alembic.ini upgrade head

# macOS / Linux
python -m alembic -c backend/alembic.ini upgrade head
```

To rollback a migration:
```bash
python -m alembic -c backend/alembic.ini downgrade -1
```

---

## 4. Backend Setup & Testing

1. Create and activate a Python virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Run the backend test suite:

```bash
python -m pytest backend/tests -v
```

4. Start the FastAPI development server:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation and probes will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Process health probe: `http://localhost:8000/health`
- Database readiness probe: `http://localhost:8000/api/v1/health/db`

---

## 5. Frontend Setup

1. Navigate to `frontend/` and install dependencies:

```bash
cd frontend
npm install
```

2. Build and verify TypeScript compilation:

```bash
npm run build
```

3. Start the Vite development server:

```bash
npm run dev
```

The frontend dashboard will be accessible at: `http://localhost:5173`.

---

## 6. Full Containerized Execution

To run both PostgreSQL and the FastAPI backend inside Docker:

```bash
docker compose up --build
```

Test the containerized health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/db
```

To stop containers:

```bash
docker compose down
```

---

## 7. Verification Commands Summary

| Action | Command |
| :--- | :--- |
| **Start Database Container** | `docker compose up -d postgres` |
| **Run Migrations** | `.venv\Scripts\python -m alembic -c backend/alembic.ini upgrade head` |
| **Rollback Migration** | `.venv\Scripts\python -m alembic -c backend/alembic.ini downgrade -1` |
| **Run Backend Tests** | `.venv\Scripts\python -m pytest backend/tests -v` |
| **Verify Process Health** | `curl http://localhost:8000/health` |
| **Verify Database Health** | `curl http://localhost:8000/api/v1/health/db` |
| **Frontend Type Check & Build** | `npm --prefix frontend run build` |
| **Start Backend Dev Server** | `uvicorn app.main:app --app-dir backend --port 8000 --reload` |
| **Start Frontend Dev Server** | `npm --prefix frontend run dev` |
