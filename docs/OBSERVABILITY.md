# Observability, Telemetry & Logging Guide (Phase 12)

## 1. Observability Pillars

DocuMind AI's bulk processing infrastructure instruments three key observability vectors:
1. **Queue Backlog & Latency:** Real-time visibility into queue depths across all four priority tiers and DLQ.
2. **Worker Fleet Metrics:** Dynamic heartbeat telemetry, resource footprint, and throughput per worker.
3. **Job Attempt Audits:** Historical execution logs, backoff schedules, and root cause exception traces.

---

## 2. Queue Telemetry

The queue status endpoint (`GET /api/v1/jobs/queue/status`) surfaces:
- `interactive_depth`: Real-time count of urgent tasks (priority 80+).
- `normal_depth`: Real-time count of standard tasks (priority 50–79).
- `bulk_depth`: Real-time count of batch tasks (priority 20–49).
- `maintenance_depth`: Real-time count of maintenance tasks (priority 0–19).
- `dead_letter_depth`: Count of exhausted failed tasks requiring inspection.
- `in_flight`: Total tasks currently leased by workers.

---

## 3. Worker Heartbeat Auditing

Each worker logs its operational status to the `worker_heartbeats` table:
```sql
SELECT worker_id, status, cpu_percent, ram_usage_mb, processed_count, failed_count, last_heartbeat
FROM worker_heartbeats
ORDER BY last_heartbeat DESC;
```

Workers report metrics every 15 seconds. If a worker goes silent for >90 seconds, the supervisory reaper marks it dead and requeues incomplete tasks.

---

## 4. Job Attempt & Failure Auditing

Whenever a job is processed, an attempt record is created in `job_attempts`:
- `attempt_number`: Sequential try counter (1, 2, 3...)
- `worker_id`: Worker executing the step
- `status`: `success` | `failed`
- `error_message`: Formatted exception summary
- `stack_trace`: Full Python traceback
- `execution_duration_ms`: Duration of attempt in milliseconds
- `created_at`: Timestamp of attempt completion

This audit trail enables instantaneous root cause analysis without scouring server logs.
