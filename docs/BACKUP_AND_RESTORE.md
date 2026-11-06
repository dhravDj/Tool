# DocuMind AI — Backup & Disaster Recovery Runbook

## 1. Overview & Service Level Objectives

The platform provides automated backup and restore mechanisms designed to meet stringent enterprise continuity requirements:
- **Recovery Point Objective (RPO):** < 1 hour (via automated hourly or daily pg_dump + storage sync).
- **Recovery Time Objective (RTO):** < 15 minutes (verified full-database and storage restoration).

---

## 2. Backup Architecture

A complete DocuMind AI backup comprises two synchronized artifacts:
1. **Relational & Vector Database:** Compressed PostgreSQL dump (`documind_db_<timestamp>.sql.gz`) with `--clean --if-exists` flags, capturing all 31 application tables, schema definitions, indexes, and vector embeddings.
2. **Physical Storage Directory:** Compressed archive (`documind_storage_<timestamp>.tar.gz`) capturing `./storage` (original files, extracted artifacts, generated thumbnails, audio clips, and video keyframes).
3. **Integrity Manifest:** Timestamped JSON manifest recording file sizes, SHA-256 checksums, and environment metadata.

---

## 3. Creating a Backup

The platform includes the production backup utility `scripts/backup_postgres.sh`:

```bash
# Run backup with default settings (auto-detects Docker or host PostgreSQL)
./scripts/backup_postgres.sh

# Or specify custom destination and database
BACKUP_DIR="/mnt/backup/documind" DB_NAME="documind" ./scripts/backup_postgres.sh
```

### Verified Sample Output:
```
================================================================================
 DocuMind AI — Automated Database & Storage Backup Subsystem
================================================================================
[+] Backup directory: ./backups
[+] Database: documind (host: localhost, port: 5432)
[*] Step 1: Performing PostgreSQL database dump...
[+] Database dump completed: ./backups/documind_db_20261107_004723.sql.gz (2.67 MB)
[*] Step 2: Archiving physical storage directory (./storage)...
[+] Storage archive completed: ./backups/documind_storage_20261107_004723.tar.gz (2.11 MB)
[*] Step 3: Generating SHA-256 integrity checksums...
[+] Checksums recorded in ./backups/checksums_20261107_004723.sha256
[*] Step 4: Generating backup manifest...
[+] Manifest written: ./backups/backup_manifest_20261107_004723.json
================================================================================
 BACKUP COMPLETED SUCCESSFULLY (Duration: 3s)
================================================================================
```

---

## 4. Restoring from a Backup

To restore the system in disaster recovery scenarios or staging migrations, use `scripts/restore_postgres.sh`:

```bash
# Restore from a specific backup timestamp into the target database
./scripts/restore_postgres.sh 20261107_004723 documind
```

### Restoration Execution Workflow:
1. **Integrity Verification:** Inspects archive gzip headers and tests extraction without writing (`tar -tzf` and `gzip -t`).
2. **Database Cleansing & Schema Import:** Connects to PostgreSQL, terminates existing connections to the target database, drops and recreates schema, and executes `pg_restore` or piped `gunzip | psql`.
3. **Storage Asset Restoration:** Unpacks storage assets into `./storage`, restoring file hierarchies and keyframes.
4. **Table Verification:** Validates that all 31 platform tables are present, non-empty, and accessible.

---

## 5. Automated Scheduling (Cron Configuration)

Configure an automated daily backup job in the host crontab (`crontab -e`):

```cron
# Daily DocuMind backup at 02:00 UTC with 30-day retention
0 2 * * * cd /opt/documind && ./scripts/backup_postgres.sh >> /var/log/documind_backup.log 2>&1
# Prune backups older than 30 days
0 3 * * * find /opt/documind/backups -type f -mtime +30 -delete
```
