#!/usr/bin/env bash
# ==============================================================================
# DocuMind AI — Production Database & Asset Backup Script (Phase 14)
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="${DB_CONTAINER:-documind-postgres}"
DB_USER="${POSTGRES_USER:-documind}"
DB_NAME="${POSTGRES_DB:-documind_db}"
STORAGE_DIR="${STORAGE_LOCAL_ROOT:-./storage}"

mkdir -p "${BACKUP_DIR}"

DB_BACKUP_FILE="${BACKUP_DIR}/documind_db_${TIMESTAMP}.sql.gz"
STORAGE_BACKUP_FILE="${BACKUP_DIR}/documind_storage_${TIMESTAMP}.tar.gz"
MANIFEST_FILE="${BACKUP_DIR}/manifest_${TIMESTAMP}.json"

echo "======================================================================"
echo " Starting DocuMind AI Backup: ${TIMESTAMP}"
echo "======================================================================"

# 1. PostgreSQL Database Dump
echo "[*] Dumping PostgreSQL database from '${DB_CONTAINER}'..."
if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip -c > "${DB_BACKUP_FILE}"
else
    echo "[!] Container ${DB_CONTAINER} not running; attempting local pg_dump..."
    pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip -c > "${DB_BACKUP_FILE}"
fi

# Verify database dump integrity
echo "[*] Verifying database archive integrity..."
gzip -t "${DB_BACKUP_FILE}"
DB_SHA256=$(sha256sum "${DB_BACKUP_FILE}" | awk '{print $1}')
DB_SIZE=$(stat -c%s "${DB_BACKUP_FILE}")
echo "[✓] Database backup created: ${DB_BACKUP_FILE} (${DB_SIZE} bytes, SHA256: ${DB_SHA256:0:16}...)"

# 2. File Storage Payload Backup
echo "[*] Archiving storage payload from '${STORAGE_DIR}'..."
if [ -d "${STORAGE_DIR}" ]; then
    tar --exclude='*.tmp' --exclude='*.lock' -czf "${STORAGE_BACKUP_FILE}" -C "$(dirname "${STORAGE_DIR}")" "$(basename "${STORAGE_DIR}")"
    gzip -t "${STORAGE_BACKUP_FILE}"
    STORAGE_SHA256=$(sha256sum "${STORAGE_BACKUP_FILE}" | awk '{print $1}')
    STORAGE_SIZE=$(stat -c%s "${STORAGE_BACKUP_FILE}")
    echo "[✓] Storage backup created: ${STORAGE_BACKUP_FILE} (${STORAGE_SIZE} bytes)"
else
    STORAGE_SHA256="none"
    STORAGE_SIZE=0
    echo "[!] Storage directory ${STORAGE_DIR} not found; skipping storage archive."
fi

# 3. Create Manifest
cat <<EOF > "${MANIFEST_FILE}"
{
  "timestamp": "${TIMESTAMP}",
  "version": "0.14.0",
  "database": {
    "file": "$(basename "${DB_BACKUP_FILE}")",
    "size_bytes": ${DB_SIZE},
    "sha256": "${DB_SHA256}",
    "db_name": "${DB_NAME}"
  },
  "storage": {
    "file": "$(basename "${STORAGE_BACKUP_FILE}")",
    "size_bytes": ${STORAGE_SIZE},
    "sha256": "${STORAGE_SHA256}"
  }
}
EOF

echo "[✓] Backup manifest saved: ${MANIFEST_FILE}"
echo "======================================================================"
echo " Backup Completed Successfully."
echo "======================================================================"
