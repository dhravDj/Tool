#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo " 1. Running Backend Quality Suite"
echo "=================================================="

echo "[*] Checking Python code formatting & linting with Ruff..."
.venv/bin/ruff check backend
echo "[*] Running static typing checks with mypy..."
(
    cd backend
    ../.venv/bin/mypy app
)
echo "[*] Executing backend unit & integration tests with pytest..."
(
    cd backend
    ../.venv/bin/pytest tests/ -v
)

echo "=================================================="
echo " 2. Running Frontend Quality Suite"
echo "=================================================="
(
    cd frontend
    echo "[*] Running TypeScript compilation check..."
    npx tsc --noEmit
    echo "[*] Executing Vitest component tests..."
    npx vitest run
)

echo "=================================================="
echo " All tests passed successfully!"
echo "=================================================="
