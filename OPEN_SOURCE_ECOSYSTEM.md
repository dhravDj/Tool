# DocuMind AI — Open-Source Ecosystem Evaluation

This document provides a comprehensive technical assessment of open-source frameworks, libraries, and tools considered for the DocuMind AI platform across all development phases.

---

## 1. Backend Foundation Candidates

| Project | Repository | Purpose | License | Activity / Status | Requirements & Compat | Hardware (CPU/GPU) | Phase | Decision & Integration Approach | Alternatives |
|---|---|---|---|---|---|---|---|---|---|
| **FastAPI** | [fastapi/fastapi](https://github.com/fastapi/fastapi) | Async ASGI REST API framework | MIT | Extremely active | Python 3.8+ (3.12+ target) | CPU only | **Phase 1 (Now)** | Adopt as primary gateway framework. Provides automatic OpenAPI docs, native async support, and high performance via Starlette. | Litestar, Sanic |
| **Pydantic** | [pydantic/pydantic](https://github.com/pydantic/pydantic) | Data parsing, validation & settings management | MIT | Extremely active (v2 Rust core) | Python 3.8+ | CPU only | **Phase 1 (Now)** | Adopt Pydantic v2 for API schemas, domain entities, and environment settings (`pydantic-settings`). High speed, strict type safety. | Marshmallow, msgspec |
| **SQLAlchemy** | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) | SQL toolkit & Object-Relational Mapper (ORM) | MIT | Active (2.0+ async series) | Python 3.7+ | CPU only | **Phase 1 (Now)** | Adopt SQLAlchemy 2.0 with async engine (`asyncpg` for PostgreSQL, `aiosqlite` for tests). Strict type annotations and declarative models. | Tortoise-ORM, SQLModel |
| **Alembic** | [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic) | Database migration tool for SQLAlchemy | MIT | Active | Python 3.8+ | CPU only | **Phase 1 (Now)** | Adopt for schema versioning, automated migrations, and repeatable deployment scripts. | yoyo-migrations |
| **Celery** | [celery/celery](https://github.com/celery/celery) | Distributed task queue | BSD-3-Clause | Active | Python 3.8+ | CPU only | **Phase 2+ (Later)** | Defer distributed task workers to Phase 2+. For Phase 1, design the task interfaces and database job tables with durable status tracking. | ARQ, SAQ, Temporal |
| **Redis** | [redis/redis](https://github.com/redis/redis) | In-memory key-value cache and message broker | RSALv2 / SSPL (or Valkey BSD) | Active | C runtime, Python client (`redis-py`) | CPU / Memory | **Phase 1 (Infrastructure)** | Containerized Redis in Docker Compose for health checks and cache/queue readiness. | Valkey, KeyDB |
| **PostgreSQL** | [postgres/postgres](https://github.com/postgres/postgres) | Relational ACID database with JSONB support | PostgreSQL License | Extremely active (PG 16/17) | C, SQL | CPU / Disk / Memory | **Phase 1 (Now)** | Primary datastore for users, files, batches, document jobs, and extraction metadata with UUID primary keys and JSONB fields. | MariaDB, SQLite |
| **MinIO** | [minio/minio](https://github.com/minio/minio) | High-performance S3-compatible object storage | AGPLv3 | Active | Go runtime | CPU / Storage | **Phase 1 (Interface) / Phase 2 (Runtime)** | Implement `StorageProviderInterface` with `LocalStorageProvider` for Phase 1 and `S3StorageProvider` adapter ready for MinIO/AWS S3. | SeaweedFS, Ceph |

---

## 2. Frontend Foundation Candidates

| Project | Repository | Purpose | License | Activity / Status | Requirements & Compat | Hardware | Phase | Decision & Integration Approach | Alternatives |
|---|---|---|---|---|---|---|---|---|---|
| **React** | [facebook/react](https://github.com/facebook/react) | Declarative UI component library | MIT | Very active (v18/v19) | Node.js 18+ | Client CPU | **Phase 1 (Now)** | Core UI framework. Component-driven architecture with clean separation of presentation and state. | Vue 3, Svelte |
| **Vite** | [vitejs/vite](https://github.com/vitejs/vite) | Next-generation frontend build tool | MIT | Extremely active (v6) | Node.js 18+ | Client CPU | **Phase 1 (Now)** | Lightning-fast HMR and optimized production bundling for TypeScript/React. | Webpack, Turbopack |
| **TypeScript** | [microsoft/TypeScript](https://github.com/microsoft/TypeScript) | Typed superset of JavaScript | Apache-2.0 | Extremely active | Node.js 18+ | Client CPU | **Phase 1 (Now)** | Full strict typing across all components, API clients, stores, and hooks. | Vanilla JS |
| **Tailwind CSS** | [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | Utility-first CSS framework | MIT | Extremely active (v3/v4) | Node.js 18+ | Client CPU | **Phase 1 (Now)** | Rapid, consistent design system implementation with responsive design and theme variable tokens. | Vanilla CSS, CSS Modules |
| **shadcn/ui** | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Accessible, reusable UI components based on Radix UI and Tailwind | MIT | Extremely active | React, Tailwind, Lucide Icons | Client CPU | **Phase 1 (Now)** | Copy/own accessible UI components (dialogs, cards, badges, buttons, tooltips) without vendor lock-in. | Chakra UI, Mantine |
| **TanStack Query** | [TanStack/query](https://github.com/TanStack/query) | Server-state management & async caching | MIT | Extremely active (v5) | React 18+ | Client CPU | **Phase 1 (Now)** | Handles all REST API requests, polling, error handling, and query caching cleanly without boilerplate. | SWR, Redux Toolkit Query |
| **Zustand** | [pmndrs/zustand](https://github.com/pmndrs/zustand) | Minimal client state management | MIT | Active | React | Client CPU | **Phase 1 (Now)** | Lightweight state store for UI theme (dark/light), sidebar collapse, and active filters. Kept minimal. | Redux, Jotai |
| **React Router** | [remix-run/react-router](https://github.com/remix-run/react-router) | Declarative client-side routing | MIT | Active (v6/v7) | React | Client CPU | **Phase 1 (Now)** | Standard SPA routing for Dashboard, Upload, Processing Jobs, File Library, Settings, and System Status. | TanStack Router |

---

## 3. Future Extraction Subprojects (Evaluation for Phase 2+)

*Note: These packages are evaluated here for architectural planning. None are installed or run in Phase 1.*

### 3.1 Document Processing Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **Docling** | [docling-project/docling](https://github.com/docling-project/docling) | Deep document parser for PDF, DOCX, PPTX, HTML to Markdown/JSON | MIT | Highly structured output, formula/table parsing, Docling Core JSON format | Large neural model weights (~1-2GB), CPU intensive | Multicore CPU or GPU (4GB+) | Phase 3 | **Primary engine** for deep structured document extraction. Wrap in an isolated worker process. |
| **MinerU** | [opendatalab/MinerU](https://github.com/opendatalab/MinerU) | High-accuracy scientific document & layout parser | Apache-2.0 | Outstanding layout recognition for academic/technical papers with equations | Heavy dependency footprint (PyTorch, Detectron2/YOLO), prefers GPU | GPU recommended (8GB+ VRAM) | Phase 3 | Optional specialized engine for scientific research papers and multi-column academic PDFs. |
| **Marker** | [datalab-to/marker](https://github.com/datalab-to/marker) | Fast PDF to Markdown conversion using specialized deep models | GPL-3.0 | Very fast high-fidelity Markdown generation | GPL-3.0 copyleft license restriction; GPU dependent | GPU (4-8GB) or heavy CPU | Phase 3 | Keep in isolated microservice/CLI worker due to GPL license boundaries to protect proprietary extensions. |
| **Unstructured** | [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | Ingestion and chunking across 20+ file formats | Apache-2.0 | Wide format coverage, standard element chunking for RAG | Heterogeneous quality across formats; large bundle size | CPU / GPU depending on strategy | Phase 2/3 | Good fallback engine for diverse unstructured documents. |
| **Apache Tika** | [apache/tika](https://github.com/apache/tika) | Universal content analysis and metadata extraction | Apache-2.0 | Battleship stability across 1,000+ legacy formats | Java runtime dependency; lacks modern AI layout understanding | Java JVM, CPU only | Phase 2 | Use via Tika Server container as universal fallback for legacy binary office and obscure formats. |

### 3.2 PDF & Vector Document Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **PyMuPDF** | [pymupdf/PyMuPDF](https://github.com/pymupdf/PyMuPDF) | High-speed C-based PDF rendering, text, vector, image extraction | AGPL-3.0 / Commercial | Extreme throughput (>100 pages/sec), minimal memory, fast metadata | AGPL license requires careful isolation or commercial license | Fast CPU, low RAM | Phase 2 | **Primary PDF parser** for fast native text extraction, page splitting, thumbnail generation, and metadata. |
| **pdfplumber** | [jsvine/pdfplumber](https://github.com/jsvine/pdfplumber) | Precise layout and table extraction from PDFs | MIT | Permissive license, visual table debugging, exact character coordinates | Slower than PyMuPDF; struggles with scanned documents | CPU, moderate RAM | Phase 2 | Secondary utility for coordinate-based table extraction and form parsing. |

### 3.3 OCR Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **PaddleOCR** | [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Multilingual text detection and recognition | Apache-2.0 | State-of-the-art accuracy, 80+ languages, table OCR, rotated text | PaddlePaddle dependency installation complexity | CPU (optimized) or GPU | Phase 3 | Recommended primary open-source OCR engine for high accuracy multilingual scans. |
| **Tesseract** | [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) | Classic LSTM-based OCR | Apache-2.0 | Ubiquitous C++ binary, small footprint, broad OS support | Low accuracy on distorted or complex background layouts | Light CPU | Phase 2 | Baseline fallback OCR for clean, high-contrast scanned documents without GPU requirements. |

### 3.4 Office Files

| Engine | Purpose | License | Strengths & Notes | Phase |
|---|---|---|---|---|
| **python-docx** | Microsoft Word (.docx) native parsing | MIT | Pure Python, fast, reliable paragraph and table extraction without Office installation. | Phase 2 |
| **openpyxl** | Microsoft Excel (.xlsx) native reading | MIT | Pure Python, memory-efficient streaming mode (`read_only=True`) for large spreadsheets. | Phase 2 |
| **python-pptx** | Microsoft PowerPoint (.pptx) extraction | MIT | Pure Python, slide-by-slide text, table, and shape extraction. | Phase 2 |
| **LibreOffice (headless)** | Legacy binary formats (.doc, .xls, .ppt, .odt) | MPL-2.0 | Invoked in headless sandbox container (`soffice --headless --convert-to pdf`) to normalize legacy formats. | Phase 3 |

### 3.5 Audio & Video Engines

| Engine | Purpose | License | Hardware | Strengths & Notes | Phase |
|---|---|---|---|---|---|
| **faster-whisper** | Speech-to-text transcription | MIT | CPU / GPU (CTranslate2) | 4x faster than vanilla Whisper, 8-bit quantization on CPU/GPU, automatic language detection. | Phase 4 |
| **FFmpeg** | Audio/video stream demuxing, transcoding, keyframe extraction | LGPL-2.1+ / GPL | CPU | Industry standard for extracting audio tracks, audio normalization, and video metadata. | Phase 4 |
| **OpenCV (headless)** | Computer vision frame extraction and image filtering | Apache-2.0 | CPU | Fast matrix operations for image pre-processing, deskewing, and keyframe selection. | Phase 4 |

### 3.6 Image, Code, Archives & Structured Data

| Category | Recommended Tool | License | Rationale | Phase |
|---|---|---|---|---|
| **Image** | **Pillow (PIL)** | HPND | Lightweight standard for image inspection, EXIF extraction, format conversion, and resizing. | Phase 2 |
| **Code** | **Tree-sitter** | MIT | Incremental syntax tree parser with AST grammar support for 40+ programming languages. | Phase 4 |
| **Archives** | **Standard Library (`zipfile`, `tarfile`) + `libarchive`** | BSD | Pure Python built-in safety for standard archives; `libarchive` for 7z, rar, cpio with zip-bomb safeguards. | Phase 2 |
| **Structured Data** | **PyArrow & Pandas** | Apache-2.0 | Memory-mapped Arrow tables for high-throughput CSV, Parquet, and TSV ingestion with zero-copy conversions. | Phase 2 |

---

## 4. Development Quality Tools

| Tool | Category | Purpose | Config File | Phase |
|---|---|---|---|---|
| **Ruff** | Python Linter & Formatter | Replaces Flake8, Black, isort in a blazing fast Rust binary | `backend/pyproject.toml` | **Phase 1** |
| **mypy** | Static Type Checker | Strict type validation for Python type annotations | `backend/pyproject.toml` | **Phase 1** |
| **pytest & pytest-asyncio** | Python Test Suite | Asynchronous unit and integration testing | `backend/pyproject.toml` | **Phase 1** |
| **ESLint** | Frontend Linter | Code quality rules for React and TypeScript | `frontend/eslint.config.js` | **Phase 1** |
| **Prettier** | Frontend Formatter | Consistent code style across TSX/CSS/JSON | `frontend/.prettierrc` | **Phase 1** |
| **Vitest** | Frontend Unit Testing | Fast Vite-native unit test runner | `frontend/vite.config.ts` | **Phase 1** |
| **React Testing Library** | Component Testing | DOM testing oriented around user interactions | `frontend/package.json` | **Phase 1** |
| **Playwright** | End-to-End Testing | Headless browser testing for real user journeys | `frontend/playwright.config.ts` (Deferred to Phase 2 for complete E2E) | **Phase 2** |
| **Docker Compose** | Infrastructure Orchestration | Single command dev and prod environment spin-up | `docker-compose.yml` | **Phase 1** |

---

## 5. Architectural Licensing & Isolation Guidelines

1. **Permissive First:** MIT, Apache-2.0, and BSD licenses are prioritized for core in-process code.
2. **Copyleft Isolation (AGPL/GPL):** Engines with AGPL (e.g. Marker, PyMuPDF) or GPL must either be used under commercially purchased licenses or isolated into separate standalone worker processes communicating over standard IPC/REST/CLI boundaries to protect the proprietary integrity of DocuMind AI.
3. **No Direct Execution:** No user-uploaded file is ever directly executed. All format engines must run in restricted subprocesses or sandbox containers with strict timeout and memory limits.
