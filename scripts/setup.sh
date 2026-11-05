#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo " DocuMind AI — Development Environment Setup"
echo "=================================================="

# 1. Environment file check
if [ ! -f .env ]; then
    echo "[+] Creating .env from .env.example..."
    cp .env.example .env
else
    echo "[*] .env file already exists."
fi

# 2. Storage directory structure
echo "[+] Ensuring storage directories exist..."
mkdir -p storage/uploads storage/temporary storage/processed storage/assets

# 3. Backend Virtual Environment
echo "[+] Configuring Python virtual environment..."
if ! command -v uv &> /dev/null; then
    echo "[!] uv not found, falling back to python3 -m venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e "backend[dev]"
else
    if [ ! -d .venv ]; then
        uv venv --python 3.13 .venv
    fi
    uv pip install --python .venv -e "backend[dev]"
fi

# 4. Frontend Dependencies
echo "[+] Installing frontend dependencies..."
if [ -d frontend ]; then
    (cd frontend && npm install)
fi

echo "=================================================="
echo " Setup complete! Ready for development."
echo " Run ./scripts/start.sh to launch the services."
echo "=================================================="
