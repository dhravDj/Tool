#!/usr/bin/env bash
set -euo pipefail

echo "[+] Running Alembic migrations for DocuMind AI..."
(
    cd backend
    ../.venv/bin/alembic upgrade head
)
echo "[*] Migrations up to date."
