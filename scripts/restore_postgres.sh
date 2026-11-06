#!/usr/bin/env bash
# ==============================================================================
# DocuMind AI — Production Database & Asset Restore Script (Phase 14)
# ==============================================================================
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path-to-db-backup.sql.gz> [path-to-storage-backup.tar.gz] [target-db-name]"
    exit 1
fi

DB_BACKUP_FILE="$1"
STORAGE_BACKUP_FILE="${2:-}"
TARGET_DB="${3:-${POSTGRES_DB:-documind_db}}"
DB_CONTAINER="${DB_CONTAINER:-documind-postgres}"
DB_USER="${POSTGRES_USER:-documind}"

echo "======================================================================"
echo " Starting DocuMind AI Restoration"
echo " Target Database: ${TARGET_DB}"
echo " Database Archive: ${DB_BACKUP_FILE}"
echo "======================================================================"

if [ ! -f "${DB_BACKUP_FILE}" ]; then
    echo "[!] Error: Backup file not found at ${DB_BACKUP_FILE}"
    exit 1
fi

# Verify archive integrity
echo "[*] Checking backup archive integrity..."
gzip -t "${DB_BACKUP_FILE}"
echo "[✓] Archive integrity verified."

# Execute database restore
echo "[*] Restoring database into '${TARGET_DB}' on container '${DB_CONTAINER}'..."
if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    gzip -dc "${DB_BACKUP_FILE}" | docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${TARGET_DB}"
else
    echo "[!] Container ${DB_CONTAINER} not running; attempting local psql restore..."
    gzip -dc "${DB_BACKUP_FILE}" | psql -U "${DB_USER}" -d "${TARGET_DB}"
fi
echo "[✓] Database tables and schemas restored successfully."

# Restore storage files if supplied
if [ -n "${STORAGE_BACKUP_FILE}" ] && [ -f "${STORAGE_BACKUP_FILE}" ]; then
    echo "[*] Restoring storage payload from ${STORAGE_BACKUP_FILE}..."
    tar -xzf "${STORAGE_BACKUP_FILE}" -C .
    echo "[✓] Storage assets restored."
fi

echo "======================================================================"
echo " Restoration Complete."
echo "======================================================================"
