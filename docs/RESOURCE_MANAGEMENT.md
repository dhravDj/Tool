# Resource Management & Backpressure Architecture (Phase 12)

## 1. System Philosophy

DocuMind AI guarantees stability under peak ingestion loads through continuous hardware telemetry, memory-bounded streaming pipelines, and active backpressure signals.

---

## 2. Resource Telemetry & HardwareGovernor

System capacity and health metrics are gathered asynchronously by `system_monitor` and `HardwareGovernor`:

| Resource Metric | Safe Threshold | Backpressure Warning | Action Triggered |
|---|---|---|---|
| **CPU Utilization** | $< 80\%$ | $\ge 85\%$ | Throttle worker spawn rate |
| **System Memory (RAM)** | $< 80\%$ | $\ge 88\%$ | Reject new batch starts; pause non-essential queues |
| **Disk Storage** | $< 85\%$ | $\ge 90\%$ | Refuse file uploads; purge temporary extraction artifacts |
| **Queue Backlog** | $< 5,000$ | $\ge 15,000$ | Ingestion backpressure mode; return HTTP 429 / Retry-After |

---

## 3. Streaming File Buffer Guarantees

Bulk file ingestion operates in streaming mode:
- Uploads bypass in-memory buffering using Python asynchronous file chunking (`chunk_size=1MB`).
- SHA-256 hashes are calculated during file write without second-pass disk reads.
- Database records are inserted in batches of 100 with explicit connection flushes to keep SQLAlchemy memory consumption constant.

---

## 4. Backpressure Status & Mitigation

When system memory or queue depth crosses warning thresholds, `SystemMonitor.is_backpressure_active()` evaluates to `True`:
1. `/api/v1/bulk/upload-stream` returns `HTTP 429 Too Many Requests` with a calculated `Retry-After: 30` header.
2. The frontend displays an alert banner notifying the user that high load has temporarily throttled ingestion.
3. Workers prioritize high-priority `interactive` and `normal` tasks before resuming background `bulk` tasks.
