# JobWatch AI — Development Guide

This guide provides instructions for setting up, running, testing, and validating JobWatch AI during **Phase 0: Architecture & Project Setup**.

---

## 1. Prerequisites

Ensure you have the following installed on your local system:

- **Python**: 3.11+ (Python 3.13 tested)
- **Node.js**: 20.x+
- **npm**: 10.x+
- **Git**: 2.40+
- **Docker & Docker Compose** (optional for containerized execution)

---

## 2. Quick Setup

### Automated Setup

**Windows (PowerShell / Command Prompt):**
```cmd
scripts\setup.bat
```

**macOS / Linux:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

## 3. Manual Step-by-Step Setup

### Step A: Environment Configuration

Copy the example environment configuration into `.env`:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Review the values in `.env`. By default, it connects the frontend at `http://localhost:5173` to the backend at `http://localhost:8000`.

### Step B: Backend Setup

1. Create and activate a Python virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Run backend tests:

```bash
python -m pytest backend/tests
```

4. Start the FastAPI development server:

```bash
# From repository root
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Step C: Frontend Setup

1. Navigate to the `frontend/` directory and install dependencies:

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

The frontend will be accessible at: `http://localhost:5173`.

---

## 4. Docker Container Execution

To run the backend inside a Docker container:

```bash
docker compose up --build
```

Test the containerized health check:

```bash
curl http://localhost:8000/health
```

To stop the container:

```bash
docker compose down
```

---

## 5. Verification Commands Summary

| Action | Command |
| :--- | :--- |
| **Run Backend Tests** | `.venv\Scripts\python -m pytest backend/tests` |
| **Verify Health Endpoint** | `curl http://localhost:8000/health` |
| **Verify API v1 Health** | `curl http://localhost:8000/api/v1/health` |
| **Frontend Type Check & Build** | `npm --prefix frontend run build` |
| **Start Backend Dev Server** | `uvicorn app.main:app --app-dir backend --port 8000 --reload` |
| **Start Frontend Dev Server** | `npm --prefix frontend run dev` |
