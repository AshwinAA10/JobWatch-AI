#!/usr/bin/env bash
set -e

echo "==================================================="
echo "Setting up JobWatch AI (Phase 0 Foundation)"
echo "==================================================="

# 1. Copy .env if not present
if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
else
    echo "[*] .env already exists."
fi

# 2. Setup Python virtual environment
if [ ! -d ".venv" ]; then
    echo "[*] Creating Python virtual environment in .venv..."
    python3 -m venv .venv
fi
echo "[*] Installing backend dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Run backend tests
echo "[*] Running backend tests..."
pytest backend/tests

# 4. Setup frontend dependencies
echo "[*] Installing frontend dependencies..."
cd frontend
npm install
npm run build
cd ..

echo "==================================================="
echo "Setup complete!"
echo ""
echo "To start backend:"
echo "  source .venv/bin/activate && uvicorn app.main:app --app-dir backend --port 8000 --reload"
echo ""
echo "To start frontend:"
echo "  cd frontend && npm run dev"
echo "==================================================="
