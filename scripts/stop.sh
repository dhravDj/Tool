#!/usr/bin/env bash
set -euo pipefail

echo "[+] Stopping DocuMind AI containers..."
docker compose down

echo "[*] All DocuMind AI services stopped."
