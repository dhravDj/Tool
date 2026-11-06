# Phase 12 Pre-Implementation Architecture & Scalability Audit

## 1. Executive Summary
This pre-implementation audit inspects the current architecture across request handling, Redis queueing, background workers, database connection pooling, storage abstractions, hardware governance, and AI indexing to prepare the platform for reliable bulk processing (10,000+ files per batch submission).

---

## 2. Component-by-Component Audit Findings

### 2.1 Request Handling & Upload Pipeline
- **Current State**: Single and multi-file detection (`/api/v1/files/detect`) uses `list[UploadFile]`. When `persist=true`, file contents are buffered and written to `local_storage`.
- **Bottlenecks & Vulnerabilities**:
  - Processing 1,000+ files in a single HTTP multipart request can overwhelm FastAPI's temporary spooling and exceed server request memory limits.
  - A single invalid file in a multi-file request causes unhandled exceptions or terminates the entire request without returning partial results.
  - No streaming batch chunking or directory structure preservation during upload.
- **Phase 12 Solution**:
  - Implement streaming multi-file ingestion with individual file validation and failure isolation.
  - Return a structured `BulkUploadManifestResponse` with per-file status (`accepted`, `rejected`, `reused`).
  - Introduce configurable batch limits: maximum files per batch (default: 10,000), max batch size (default: 10 GB), max file size (default: 500 MB).

---

### 2.2 Redis Task Queue & Worker Execution
- **Current State**: `TaskQueue` in `backend/app/infrastructure/queue/redis.py` uses simple Redis lists (`rpush`/`blpop` on `queue:{name}`). Retries simply re-push to the same queue without backoff delay.
- **Bottlenecks & Vulnerabilities**:
  - **No Priority Levels**: Bulk background jobs compete equally with interactive user queries, risking queue starvation for foreground users.
  - **Immediate Retries**: Retrying tasks immediately upon failure causes thundering herds and rapid exhaustion of retry limits during transient downtime.
  - **Missing Stale Job Recovery**: If a worker crashes or encounters an OOM kill while processing a task, the task remains perpetually stuck in `"processing"`.
  - **Lack of Idempotency Keys**: Duplicate enqueue requests create duplicate background executions.
- **Phase 12 Solution**:
  - Multi-tier priority queues: `interactive` (priority 80), `normal` (priority 50), `bulk` (priority 30), and `maintenance` (priority 10).
  - Exponential backoff with randomized jitter (`initial_delay * (2 ** retry_count) + random(0, 1)`).
  - Worker heartbeats (`WorkerHeartbeatRecord`) and periodic stale-job reaper re-queueing jobs orphaned by crashed workers.
  - Idempotency key tracking in Redis and PostgreSQL.

---

### 2.3 Database Scalability & Connection Pooling
- **Current State**: PostgreSQL 16 with SQLAlchemy async engine (`pool_recycle=1800`, `pool_timeout=15`).
- **Bottlenecks & Vulnerabilities**:
  - Inserting 10,000 records in a single database transaction risks lock contention, prolonged transactions, and memory pressure.
  - Loading large sets of ORM models into memory causes high RSS consumption and N+1 query overhead.
- **Phase 12 Solution**:
  - Chunked database inserts (50–100 items per flush).
  - Bounded transaction scopes: individual job state transitions commit in isolated, short transactions.
  - Cursor- and offset-based pagination on batch file listings.
  - Indexed composite lookups on `(batch_id, status)` and `(file_id, status)`.

---

### 2.4 Hardware Governance & GPU Mutex
- **Current State**: `HardwareGovernor` enforces `MAX_PARALLEL_WORKERS = 4` (CPU semaphore) and `GPU_MAX_CONCURRENT_INFERENCE = 1` (GPU mutex for RTX 3050 4GB).
- **Bottlenecks & Vulnerabilities**:
  - Bulk processing could saturate CPU slots, delaying interactive extraction.
  - Background AI indexing could monopolize the GPU mutex if not prioritized.
- **Phase 12 Solution**:
  - Separate concurrency budgets for generic CPU tasks vs GPU-intensive tasks vs embedding calls.
  - Bounded concurrency with backpressure when queue depth exceeds threshold.

---

### 2.5 Storage Subsystem & Deduplication
- **Current State**: `LocalStorageProvider` contains directory traversal guards and partitioned folders.
- **Bottlenecks & Vulnerabilities**:
  - No automated content deduplication at ingest: identical files uploaded by the same user consume duplicate disk space and trigger redundant extractions.
  - Temporary files from cancelled or abandoned uploads could accumulate.
- **Phase 12 Solution**:
  - SHA-256 pre-check: If identical file content has already been successfully extracted for the user, reuse previous analysis unless `force=true`.
  - Content-addressed reference tracking with strict per-user authorization boundaries.
  - Automated cleanup routine for abandoned temporary uploads.

---

## 3. Implementation Plan
1. **Database Migration `011_bulk_processing_records`**: Add `processing_batches`, `batch_files`, `processing_jobs`, `job_attempts`, `worker_heartbeats`.
2. **Priority Task Queue & Scalable Worker**: Multi-level priority, jittered exponential backoff, worker heartbeats, stale job recovery.
3. **Pipeline Orchestrator & Batch Manager**: Multi-stage pipeline, pause/resume/cancel/retry-failed, idempotency.
4. **Deduplication & Storage Scalability**: Streaming upload handler, SHA-256 deduplication, per-user quotas.
5. **REST API (19 Endpoints)**: Bulk upload, batches, jobs, capacity, system health.
6. **Frontend Integration**: BulkUploadView, BatchProcessingView, JobMonitorView, ProcessingAnalyticsView, route `/bulk-processing`.
7. **Load Tests**: 100, 500, 1,000, 5,000, and 10,000 file verification.
8. **Verification & Regression**: Ensure all 248 existing tests continue to pass.
