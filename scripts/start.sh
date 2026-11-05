#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-docker}"

if [ "$MODE" = "docker" ]; then
    echo "[+] Starting DocuMind AI services via Docker Compose..."
    docker compose up -d postgres redis
    echo "[*] Waiting for PostgreSQL and Redis to become healthy..."
    docker compose ps
    echo "[+] Launching backend and frontend containers..."
    docker compose up -d backend frontend
    echo "[*] Services started. Gateway at http://localhost:8000 | Dashboard at http://localhost:5173"
elif [ "$MODE" = "local" ]; then
    echo "[+] Starting local development servers..."
    echo "[*] Starting PostgreSQL & Redis via Docker..."
    docker compose up -d postgres redis
    echo "[*] Starting FastAPI Backend on http://localhost:8000..."
    (.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend) &
    BACKEND_PID=$!
    echo "[*] Starting Vite Frontend on http://localhost:5173..."
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!

    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM
    wait
else
    echo "Usage: $0 [docker|local]"
    exit 1
fi
