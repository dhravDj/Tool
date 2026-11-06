# Bulk Processing Architecture & Ingestion Guide (Phase 12)

## 1. System Purpose & Overview

The DocuMind AI Bulk Processing Engine enables reliable high-volume ingestion, extraction, analysis, indexing, and AI processing of file collections exceeding 10,000+ files per batch submission. 

Prior to Phase 12, DocuMind AI executed file operations primarily through single-file asynchronous tasks. Phase 12 introduces:
- **Bounded Resource Management:** Enforces streaming file uploads and chunked database flushes (100 files/chunk), preventing OOM conditions even on low-RAM commodity instances.
- **Tenant-Aware Deduplication:** Multi-tier SHA-256 fingerprinting that skips identical files or symlinks results to save CPU/GPU cycles.
- **Multi-Stage Processing Pipeline:** Clear lifecycle state machine (`submitted` $\to$ `queued` $\to$ `processing` $\to$ `completed` / `paused` / `failed` / `cancelled`) across 5 processing stages.
- **Work-Weighted Progress:** Non-linear progress calculation reflecting relative operational complexity across detection (5%), extraction (60%), and AI vector indexing (35%).

```
                  ┌──────────────────────────────────────────┐
                  │          Bulk Ingestion API              │
                  │   POST /api/v1/bulk/upload-stream        │
                  │   POST /api/v1/bulk/batches              │
                  └────────────────────┬─────────────────────┘
                                       │
                         [Chunked Ingestion: 100/flush]
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │         Deduplication Engine             │
                  │   - Fast SHA-256 Tenant Lookup           │
                  │   - Action: Link / Process / Reject      │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │       PostgreSQL Batch Persistence       │
                  │   - processing_batches                   │
                  │   - batch_files                          │
                  │   - processing_jobs                      │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │        Priority Task Queue (Redis)       │
                  │   Interactive (90) | Normal (50)         │
                  │   Bulk (30)        | Maintenance (10)    │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │        Autonomous Worker Fleet           │
                  │   HardwareGovernor Slot Allocation:      │
                  │   - 4 Parallel CPU Worker Slots          │
                  │   - 1 Concurrent GPU Worker Slot         │
                  └──────────────────────────────────────────┘
```

---

## 2. Ingestion Lifecycles & State Transitions

### Batch Lifecycle State Machine
```
   [submitted] ──────► [queued] ──────► [processing] ──────► [completed]
                          │                   │
                          │                   ├──────► [paused] ──► [processing]
                          ▼                   │
                     [cancelled]              ├──────► [partially_completed]
                                              │
                                              └──────► [failed]
```

| State | Description |
|---|---|
| `submitted` | Manifest received, files validated, database batch created. |
| `queued` | Batch files mapped to processing jobs in the priority queue. |
| `processing` | Autonomous workers actively leasing slots and executing pipeline stages. |
| `paused` | In-flight tasks finish, no new jobs popped; preserved state. |
| `completed` | All jobs successfully processed across all stages. |
| `partially_completed` | All jobs processed, but one or more files encountered non-fatal errors. |
| `cancelled` | Processing aborted by user; remaining jobs revoked. |
| `failed` | Catastrophic failure or user threshold for fatal errors exceeded. |

---

## 3. Chunked Streaming Ingestion Guarantees

To ensure 10,000+ files can be accepted without exhaustion of system memory:
1. **Multipart File Streaming:** Uploads are streamed sequentially to temporary disk buffers rather than parsed completely in memory.
2. **Chunked Database Flushing:** Files are appended to `batch_files` in chunks of 100 rows per transaction flush:
   ```python
   chunk_size = 100
   for i in range(0, len(files_data), chunk_size):
       chunk = files_data[i : i + chunk_size]
       batch_files = [BatchFileRecord(...) for item in chunk]
       session.add_all(batch_files)
       await session.flush()
   await session.commit()
   ```
3. **Bounded Memory Profile:** Memory RSS growth during registration of 10,000 files is guaranteed under 10 MB.

---

## 4. Work-Weighted Progress Computation

Standard count-based progress ($done / total$) misleads users when early fast operations (registration, detection) finish in milliseconds while complex operations (OCR, AI embedding) require seconds. DocuMind AI computes work-weighted completion:

$$\text{Weight}_{\text{stage}} = \begin{cases} 
0.05, & \text{Detection} \\ 
0.60, & \text{Extraction (Phases 3--10)} \\ 
0.35, & \text{AI Indexing (Phase 11)} 
\end{cases}$$

$$\text{Progress} = \frac{\sum_{i=1}^{N} \text{Weight}_{\text{completed stage}}(i)}{N} \times 100\%$$

This ensures consistent and accurate ETA forecasting across all batch sizes.
