# DocuMind AI — Operations & Incident Response Runbook

## 1. System Services & Architecture Map

| Service Name | Port | Description | Health Endpoint |
|---|---|---|---|
| `nginx-edge` | 80 / 443 | Ingress reverse proxy, SSL termination, static SPA | `GET /` |
| `documind-api` | 8000 | FastAPI backend API | `GET /api/v1/health` |
| `documind-worker` | - | Background task processing workers | CLI / Heartbeat |
| `documind-postgres` | 5432 | Primary relational & vector database | `pg_isready` |
| `documind-redis` | 6379 | Task queue broker & cache | `redis-cli ping` |

---

## 2. Health Monitoring & Key Performance Metrics

### A. Health Checks
Check system status periodically or integrate with uptime monitoring (Prometheus, Datadog, UptimeKuma):

```bash
# Full platform health check
curl -f -s http://localhost:8000/api/v1/health | jq .

# Database connectivity check
docker exec documind-postgres pg_isready -U documind

# Redis broker responsiveness check
docker exec documind-redis redis-cli ping
```

### B. Priority Task Queue Monitoring
Monitor queue depths and worker utilization:

```bash
# Inspect queue lengths across tiers
curl -s http://localhost:8000/api/v1/bulk/system-capacity | jq .
```

---

## 3. Incident Playbooks

### Playbook A: Worker Backpressure & High Queue Depth
- **Symptom:** Queue depth exceeds 500 tasks; processing latency spikes; batch completion delayed.
- **Root Cause:** Ingestion rate exceeds worker processing throughput or long-running video/audio tasks are hogging workers.
- **Remediation:**
  1. Check worker logs: `docker compose -f docker-compose.prod.yml logs --tail=100 backend`.
  2. Scale worker processes: `docker compose -f docker-compose.prod.yml up -d --scale backend=4`.
  3. Verify system CPU and memory: `docker stats`.

### Playbook B: Worker Out-Of-Memory (OOM) Crash
- **Symptom:** Worker container exits with code 137; tasks remain in unacknowledged state.
- **Root Cause:** Processing unusually large archive or ultra-high-resolution image/video.
- **Remediation:**
  1. Automated lease recovery returns stranded tasks to the priority queue after visibility timeout expires.
  2. Inspect failed task ID and offending file record in the database.
  3. Verify file constraints (`MAX_IMAGE_PIXELS`, `ARCHIVE_MAX_TOTAL_UNCOMPRESSED_BYTES`).
  4. Adjust container memory reservation in `docker-compose.prod.yml`.

### Playbook C: Database Connection Saturation
- **Symptom:** API returns HTTP 500 with `TimeoutError: QueuePool limit of size 20 overflow 10 reached`.
- **Root Cause:** Spike in concurrent requests or long-running queries holding connections.
- **Remediation:**
  1. Inspect active database connections:
     `docker exec documind-postgres psql -U documind -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"`
  2. Tune connection pool in `.env.production`:
     `DATABASE_POOL_SIZE=30`, `DATABASE_MAX_OVERFLOW=20`.
  3. Restart backend service: `docker compose -f docker-compose.prod.yml restart backend`.

---

## 4. Log Inspection & Troubleshooting

```bash
# Follow live API logs with correlation IDs
docker compose -f docker-compose.prod.yml logs -f --tail=200 backend

# Search for specific error or correlation ID
docker compose -f docker-compose.prod.yml logs backend | grep "CORR-ID-12345"

# Inspect Nginx edge access and error logs
docker compose -f docker-compose.prod.yml logs nginx
```
