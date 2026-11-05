# DocuMind AI — Technical Architecture Decision Records (ADR)

This document records the foundational architectural decisions, rationale, alternatives considered, and trade-offs made for DocuMind AI.

---

## ADR-001: Modular Monolith vs. Distributed Microservices

### Status
**Accepted** (Phase 1)

### Context
DocuMind AI aims to be a universal file intelligence platform supporting file ingestion, format detection, multimodal extraction, AI understanding, and structured export. The system must support thousands of files per batch while remaining easy to develop, deploy, and maintain.

### Decision
Adopt a **Modular Monolith** architecture for Phase 1 and initial releases. The codebase is organized into bounded contexts (`files`, `formats`, `extraction`, `ai`, `batches`, `exports`) sharing a unified application gateway (FastAPI) and clean database schema, with strict dependency rules enforced at code level.

### Rationale
- Premature microservices introduce high operational overhead (distributed transactions, network latency, complex observability, service discovery, duplicate deployments).
- Well-defined domain boundaries with dependency inversion allow extracting high-load modules (e.g. CPU/GPU extraction workers) into standalone microservices in later phases without rewriting core business logic.

### Trade-offs
- Components share the same runtime memory space during development.
- Monolith requires discipline to prevent tight cross-module coupling.

---

## ADR-002: SQLAlchemy 2.0 Async ORM with PostgreSQL and UUID Primary Keys

### Status
**Accepted** (Phase 1)

### Context
The platform must record high volumes of file metadata, batch states, document jobs, extraction outputs, and system configurations with strict ACID guarantees, high-throughput concurrent writes, and flexible metadata schemas.

### Decision
- Standardize on **PostgreSQL** (version 16+) as the primary relational database.
- Use **SQLAlchemy 2.0 Async Engine** paired with `asyncpg` for high-throughput asynchronous I/O.
- Use **UUIDv4** for all primary keys to guarantee global uniqueness, prevent sequential enumeration attacks, and simplify future sharding or distributed ingestion.
- Use **JSONB** columns for flexible engine metadata and extraction parameters.
- Manage database evolution using **Alembic** migrations.

### Rationale
- `asyncpg` offers industry-leading query throughput on asynchronous Python event loops.
- UUID keys allow clients or edge ingestors to pre-generate IDs if necessary.
- PostgreSQL JSONB provides indexable semi-structured document storage inside a relational model.

---

## ADR-003: Plugin & Adapter Architecture via Python Abstract Base Classes (ABCs)

### Status
**Accepted** (Phase 1)

### Context
DocuMind AI must support dozens of file formats (PDF, DOCX, XLSX, audio, images, archives) and multiple extraction engines (PyMuPDF, Docling, MinerU, Whisper, Tesseract) and AI providers (Ollama, vLLM, OpenAI, Gemini, Anthropic) without hardcoding engine logic into the core orchestration pipeline.

### Decision
Implement explicit Abstract Base Classes (ABCs) in `backend/app/plugins/interfaces/`:
- `FileDetectorInterface`: Format and MIME identification.
- `ExtractionEngineInterface`: Normalized document parsing and text/element extraction.
- `AIProviderInterface`: Local and cloud LLM/VLM inference abstraction.
- `StorageProviderInterface`: Storage operations (local disk vs. S3/MinIO).
- `OutputFormatterInterface`: Serializing extracted data into Markdown, JSON, Text, etc.
- `ProcessingPluginInterface`: Complete plugin lifecycle, dependency checks, and metadata.

A thread-safe `PluginRegistry` manages registration, capability lookup, and fallback resolution.

### Rationale
- New extraction engines can be developed and plugged in without altering existing ingestion routes or database models.
- Mock plugins can be registered during Phase 1 to thoroughly test the orchestration interface without installing gigabytes of neural weights.

---

## ADR-004: Local-First AI Strategy with Cloud Fallback Abstraction

### Status
**Accepted** (Phase 1)

### Context
File intelligence often involves sensitive, confidential documents (legal contracts, financial statements, medical records). Users must have full control over data residency and privacy.

### Decision
- Configure **Local Processing** as the default mode (`AI_MODE=local`, `CLOUD_PROCESSING_ENABLED=false`).
- Isolate all LLM/VLM interactions behind `AIProviderInterface`.
- Cloud AI providers require explicit opt-in via environment configuration and user consent flags.
- Support lazy CPU fallback when NVIDIA GPU or CUDA drivers are unavailable.

### Rationale
- Guarantees strict data sovereignty for air-gapped or privacy-conscious deployments.
- Pluggable provider interface allows seamless switching between Ollama, local models, and cloud APIs.

---

## ADR-005: Relational Parent-Child Batch and Job Hierarchy

### Status
**Accepted** (Phase 1)

### Context
Users will upload batches containing from a single file up to 10,000+ files. The system must track overall batch progress while executing individual document jobs with independent retry and failure domains.

### Decision
Implement a two-tier execution model in the database:
- `batches`: Holds aggregate counters (`total_files`, `completed_files`, `failed_files`, `status`), batch metadata, and owner reference.
- `document_jobs`: Represents the granular processing state for an individual file within a batch (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`), recording attempt counts, specific error codes, and execution timings.

### Rationale
- Failure in extracting one file does not halt or corrupt the rest of the batch.
- High-volume progress polling can query aggregate batch counters efficiently or inspect individual failed jobs.

---

## ADR-006: Frontend Technology Stack (React, Vite, TypeScript, Tailwind CSS, TanStack Query)

### Status
**Accepted** (Phase 1)

### Context
The frontend needs to be a responsive, accessible, high-performance web dashboard providing file management, batch progress monitoring, job logs, and system settings.

### Decision
- **Vite** + **React 19** + **TypeScript** for the core SPA.
- **Tailwind CSS** with CSS variables for responsive styling and instant light/dark mode support.
- **TanStack Query (React Query v5)** for server state caching, background polling, and optimistic updates.
- **React Router v6/v7** for client-side routing.
- **Zustand** strictly reserved for lightweight client UI state (sidebar toggling, theme preference).

### Rationale
- Zero unnecessary boilerplate; avoids heavy global Redux state for data that belongs in server cache.
- Standardized UI components modeled after accessible Radix / shadcn principles ensure high usability.

---

## ADR-007: Storage Layer Abstraction (Local Filesystem with Object Storage Ready)

### Status
**Accepted** (Phase 1)

### Context
Files must be safely stored across their lifecycle: incoming upload -> temporary working scratchpad -> processed outputs -> long-term storage.

### Decision
Abstract storage behind `StorageProviderInterface`. Provide `LocalStorageProvider` for Phase 1 storing files in organized directories (`storage/uploads/`, `storage/temporary/`, `storage/processed/`, `storage/assets/`), with filename hashing (SHA-256) and directory partitioning to avoid OS file count bottlenecks. Ensure the interface maps 1:1 to S3/MinIO bucket operations for seamless cloud adoption.

### Rationale
- Local development requires zero external S3 setup.
- Transitioning to MinIO or AWS S3 in production requires merely switching the configured provider.
