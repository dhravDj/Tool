# DocuMind AI — Production Readiness Guide (Phases 1 to 4)

## 1. System Overview

DocuMind AI is a sovereign, multi-stage universal file intelligence platform.
The platform operates as a modular monolith with decoupled engine subsystems:

```
[ Upload Ingestion ]
         │
         ▼
[ Phase 2: Universal File Detection Engine ] (Multi-signal arbitration, <3ms)
         │
         ├─── If Document (PDF, DOCX, DOC, TXT, MD, RTF, ODT, EPUB)
         │           ▼
         │    [ Phase 3: Document Extraction Engine ] (Native structural extraction, OCR fallback)
         │
         └─── If Image (PNG, JPEG, WEBP, BMP, TIFF, SVG)
                     ▼
              [ Phase 4: Image & Visual Intelligence ] (Sub-8ms deskew, OCR, Heuristic CV, Grounded VQA)
```

Hardware bounds and queue execution are governed centrally by **Phase 1 Infrastructure** (`HardwareGovernor` and `TaskQueue`).

---

## 2. Target Hardware Profile & Configuration

DocuMind AI is optimized for local sovereignty on modern workstation hardware:
- **Target CPU:** AMD Ryzen 7 5800H (8 physical cores / 16 threads).
- **Target GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM).
- **Worker Configuration (`backend/app/core/config.py`):**
  - `MAX_PARALLEL_WORKERS = 4` (leaves remaining host cores for system responsiveness).
  - `GPU_MAX_CONCURRENT_INFERENCE = 1` (strict mutex preventing CUDA OOM on 4GB VRAM).
  - `VISION_ENGINE_DEFAULT = "documind-heuristic-cv-v1"` (deterministic, zero neural overhead).
  - `VISION_DEVICE = "cpu"` (transparent CPU fallback).

---

## 3. Production Environment Checklist

### 3.1 PostgreSQL Database
- **Connection URL:** Configured via `DATABASE_URL` environment variable.
- **Connection Pool:**
  - `pool_size = 10`
  - `max_overflow = 20`
  - `pool_recycle = 1800` (automatically recycles connections idle for 30 minutes).
  - `pool_timeout = 15` (prevents indefinite blocking under connection spikes).
  - `pool_pre_ping = True` (detects dropped TCP sockets before query execution).
- **Migrations:** Managed via Alembic (`alembic upgrade head`).

### 3.2 Redis Task Queue & Caching
- **Redis URI:** Configured via `REDIS_URL`.
- **Resilience:** If Redis is offline or unreachable, `TaskQueue` falls back transparently to in-memory asynchronous queues without crashing or losing incoming tasks.
- **Worker Process:** Start background workers using `app.workers.task_worker.task_worker.start()`.

### 3.3 Storage Configuration
- **Backend:** `STORAGE_BACKEND = "local"` (or `"s3"`).
- **Root Directory:** Default `./storage`. Ensure persistent volume mount with `0750` permissions.
- **Path Traversal Protection:** Enforced by `_resolve_safe_path()` in `local_storage.py`.

---

## 4. Vision & Intelligence Classification Policy

To maintain complete transparency and technical veracity:
- **Heuristic CV Classification:** All visual layout profiling, luminance distribution, Otsu binarization, palette extraction, and keyword topology matching are explicitly reported as **`engine_type="heuristic"`** under the name **`documind-heuristic-cv-v1`**.
- **Zero Hallucination:** Heuristic algorithms must never be represented to users or APIs as deep neural model inference.
- **Extensible Adapters:** Teams wishing to enable local neural models (ONNX) or cloud VLMs (Gemini / OpenAI) can register implementations of `VisionAdapterInterface`.

---

## 5. Deployment & Health Verification

Run the unified quality and verification suite before every deployment:
```bash
./scripts/run_tests.sh
```

Execute the comprehensive performance and accuracy benchmark:
```bash
.venv/bin/python scripts/evaluate_phases_1_to_4.py
```

Inspect the system health endpoint:
```http
GET /api/v1/health
```
Returns PostgreSQL connectivity, Redis status, storage path availability, active plugin count, and hardware governor status.
