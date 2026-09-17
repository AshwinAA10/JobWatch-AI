@echo off
echo ===================================================
echo Setting up JobWatch AI (Phase 1 Foundation)
echo ===================================================

REM 1. Copy .env if not present
if not exist ".env" (
    echo [*] Creating .env from .env.example...
    copy .env.example .env
) else (
    echo [*] .env already exists.
)

REM 2. Setup Python virtualenv
if not exist ".venv" (
    echo [*] Creating Python virtual environment in .venv...
    python -m venv .venv
)
echo [*] Installing backend dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

REM 3. Run backend tests
echo [*] Running backend tests...
python -m pytest backend\tests -v

REM 4. Setup frontend dependencies
echo [*] Installing frontend dependencies...
cd frontend
call npm install
call npm run build
cd ..

echo ===================================================
echo Setup complete!
echo.
echo To start database:
echo   docker compose up -d postgres
echo.
echo To apply migrations:
echo   .venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
echo.
echo To start backend:
echo   .venv\Scripts\uvicorn app.main:app --app-dir backend --port 8000 --reload
echo.
echo To start frontend:
echo   cd frontend ^&^& npm run dev
echo ===================================================
