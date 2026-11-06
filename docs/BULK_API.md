# Bulk Processing REST API Specification (Phase 12)

All endpoints are mounted under `/api/v1/bulk`, `/api/v1/jobs`, and `/api/v1/system`.

## 1. Bulk Processing Endpoints (`/api/v1/bulk`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/batches` | Creates a new processing batch manifest |
| `GET` | `/batches` | Lists batches with pagination and state filtering |
| `GET` | `/batches/{id}` | Retrieves batch details and work-weighted progress |
| `POST` | `/batches/{id}/start` | Transitions batch to `processing` and enqueues jobs |
| `POST` | `/batches/{id}/pause` | Pauses active batch execution |
| `POST` | `/batches/{id}/resume` | Resumes a paused batch |
| `POST` | `/batches/{id}/cancel` | Cancels batch processing and revokes pending jobs |
| `POST` | `/batches/{id}/retry-failed` | Re-queues only failed files in a batch |
| `GET` | `/batches/{id}/files` | Lists files in batch with status and dedup results |
| `GET` | `/batches/{id}/audit` | Generates comprehensive JSON audit report |
| `POST` | `/upload-stream` | Streams multiple files directly into a new batch |
| `POST` | `/dedup/inspect` | Dry-run duplicate check without creating records |

---

## 2. Job & Queue Endpoints (`/api/v1/jobs`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/submit` | Enqueues a standalone task with custom priority |
| `GET` | `/{id}` | Retrieves processing job status, stage, and attempts |
| `POST` | `/{id}/cancel` | Revokes a pending or running job |
| `POST` | `/{id}/retry` | Manually retries a failed job |
| `GET` | `/{id}/attempts` | Returns execution history and failure logs |
| `GET` | `/queue/status` | Returns depths of all priority tiers and DLQ |

---

## 3. System Telemetry Endpoints (`/api/v1/system`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/processing-capacity` | Returns active worker limits, GPU slots, and backpressure state |
| `GET` | `/worker-status` | Lists all registered autonomous workers and heartbeats |
| `GET` | `/resource-usage` | Returns CPU, RAM, and Disk storage utilization |

---

## 4. Example Requests & Responses

### `POST /api/v1/bulk/batches`
Creates a batch record:
```json
{
  "name": "Q4 Financial Reports Ingestion",
  "policy": {
    "priority": 30,
    "max_parallel_workers": 4,
    "continue_on_failure": true,
    "deduplication_mode": "skip"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "e2c72bbf-1d89-4a0b-93ff-183427909c25",
    "name": "Q4 Financial Reports Ingestion",
    "status": "submitted",
    "total_files": 0,
    "progress_percent": 0.0,
    "created_at": "2026-11-06T18:30:00Z"
  },
  "error": null
}
```

### `GET /api/v1/system/processing-capacity`
Returns host capacity and throttling flags:
```json
{
  "success": true,
  "data": {
    "max_parallel_cpu_workers": 4,
    "max_concurrent_gpu_slots": 1,
    "active_cpu_workers": 2,
    "active_gpu_workers": 0,
    "backpressure_active": false,
    "queue_depth_total": 450
  },
  "error": null
}
```
