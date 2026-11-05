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
| **Celery** | [celery/celery](https://github.com/celery/celery) | Distributed task queue | BSD-3-Clause | Active | Python 3.8+ | CPU only | **Phase 3+ (Later)** | Defer distributed task workers to Phase 3+. For Phase 1 & 2, task interfaces and database job tables provide durable state tracking. | ARQ, SAQ, Temporal |
| **Redis** | [redis/redis](https://github.com/redis/redis) | In-memory key-value cache and message broker | RSALv2 / SSPL (or Valkey BSD) | Active | C runtime, Python client (`redis-py`) | CPU / Memory | **Phase 1 (Infrastructure)** | Containerized Redis in Docker Compose for health checks and cache/queue readiness. | Valkey, KeyDB |
| **PostgreSQL** | [postgres/postgres](https://github.com/postgres/postgres) | Relational ACID database with JSONB support | PostgreSQL License | Extremely active (PG 16/17) | C, SQL | CPU / Disk / Memory | **Phase 1 (Now)** | Primary datastore for users, files, batches, document jobs, and extraction metadata with UUID primary keys and JSONB fields. | MariaDB, SQLite |
| **MinIO** | [minio/minio](https://github.com/minio/minio) | High-performance S3-compatible object storage | AGPLv3 | Active | Go runtime | CPU / Storage | **Phase 1 (Interface) / Phase 3 (Runtime)** | Implement `StorageProviderInterface` with `LocalStorageProvider` for Phase 1/2 and `S3StorageProvider` adapter ready for MinIO/AWS S3. | SeaweedFS, Ceph |

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

## 3. Future Extraction Subprojects (Evaluation for Phase 3+)

*Note: These packages are evaluated here for architectural planning. None are installed or run in Phase 1 or Phase 2.*

### 3.1 Document Processing Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **Docling** | [docling-project/docling](https://github.com/docling-project/docling) | Deep document parser for PDF, DOCX, PPTX, HTML to Markdown/JSON | MIT | Highly structured output, formula/table parsing, Docling Core JSON format | Large neural model weights (~1-2GB), CPU intensive | Multicore CPU or GPU (4GB+) | Phase 3 | **Primary engine** for deep structured document extraction. Wrap in an isolated worker process. |
| **MinerU** | [opendatalab/MinerU](https://github.com/opendatalab/MinerU) | High-accuracy scientific document & layout parser | Apache-2.0 | Outstanding layout recognition for academic/technical papers with equations | Heavy dependency footprint (PyTorch, Detectron2/YOLO), prefers GPU | GPU recommended (8GB+ VRAM) | Phase 3 | Optional specialized engine for scientific research papers and multi-column academic PDFs. |
| **Marker** | [datalab-to/marker](https://github.com/datalab-to/marker) | Fast PDF to Markdown conversion using specialized deep models | GPL-3.0 | Very fast high-fidelity Markdown generation | GPL-3.0 copyleft license restriction; GPU dependent | GPU (4-8GB) or heavy CPU | Phase 3 | Keep in isolated microservice/CLI worker due to GPL license boundaries to protect proprietary extensions. |
| **Unstructured** | [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | Ingestion and chunking across 20+ file formats | Apache-2.0 | Wide format coverage, standard element chunking for RAG | Heterogeneous quality across formats; large bundle size | CPU / GPU depending on strategy | Phase 3 | Good fallback engine for diverse unstructured documents. |
| **Apache Tika** | [apache/tika](https://github.com/apache/tika) | Universal content analysis and metadata extraction | Apache-2.0 | Battleship stability across 1,000+ legacy formats | Java runtime dependency; lacks modern AI layout understanding | Java JVM, CPU only | Phase 3 | Use via Tika Server container as universal fallback for legacy binary office and obscure formats. |

### 3.2 PDF & Vector Document Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **PyMuPDF** | [pymupdf/PyMuPDF](https://github.com/pymupdf/PyMuPDF) | High-speed C-based PDF rendering, text, vector, image extraction | AGPL-3.0 / Commercial | Extreme throughput (>100 pages/sec), minimal memory, fast metadata | AGPL license requires careful isolation or commercial license | Fast CPU, low RAM | Phase 3 | **Primary PDF parser** for fast native text extraction, page splitting, thumbnail generation, and metadata. |
| **pdfplumber** | [jsvine/pdfplumber](https://github.com/jsvine/pdfplumber) | Precise layout and table extraction from PDFs | MIT | Permissive license, visual table debugging, exact character coordinates | Slower than PyMuPDF; struggles with scanned documents | CPU, moderate RAM | Phase 3 | Secondary utility for coordinate-based table extraction and form parsing. |

### 3.3 OCR Engines

| Engine | Repository | Capabilities | License | Strengths | Limitations | Hardware Req | Phase Target | Integration Recommendation |
|---|---|---|---|---|---|---|---|---|
| **PaddleOCR** | [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Multilingual text detection and recognition | Apache-2.0 | State-of-the-art accuracy, 80+ languages, table OCR, rotated text | PaddlePaddle dependency installation complexity | CPU (optimized) or GPU | Phase 3 | Recommended primary open-source OCR engine for high accuracy multilingual scans. |
| **Tesseract** | [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) | Classic LSTM-based OCR | Apache-2.0 | Ubiquitous C++ binary, small footprint, broad OS support | Low accuracy on distorted or complex background layouts | Light CPU | Phase 3 | Baseline fallback OCR for clean, high-contrast scanned documents without GPU requirements. |

### 3.4 Office Files

| Engine | Purpose | License | Strengths & Notes | Phase |
|---|---|---|---|---|
| **python-docx** | Microsoft Word (.docx) native parsing | MIT | Pure Python, fast, reliable paragraph and table extraction without Office installation. | Phase 3 |
| **openpyxl** | Microsoft Excel (.xlsx) native reading | MIT | Pure Python, memory-efficient streaming mode (`read_only=True`) for large spreadsheets. | Phase 3 |
| **python-pptx** | Microsoft PowerPoint (.pptx) extraction | MIT | Pure Python, slide-by-slide text, table, and shape extraction. | Phase 3 |
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
| **Image** | **Pillow (PIL)** | HPND | Lightweight standard for image inspection, EXIF extraction, format conversion, and resizing. | Phase 3 |
| **Code** | **Tree-sitter** | MIT | Incremental syntax tree parser with AST grammar support for 40+ programming languages. | Phase 4 |
| **Archives** | **Standard Library (`zipfile`, `tarfile`) + `libarchive`** | BSD | Pure Python built-in safety for standard archives; `libarchive` for 7z, rar, cpio with zip-bomb safeguards. | Phase 3 |
| **Structured Data** | **PyArrow & Pandas** | Apache-2.0 | Memory-mapped Arrow tables for high-throughput CSV, Parquet, and TSV ingestion with zero-copy conversions. | Phase 3 |

---

## 4. Phase 2 Universal File Detection Candidates Evaluation

| Candidate | Repository / Origin | Purpose | License | Maintenance & Activity | Dependencies | Platform Compatibility | Detection Coverage | Limitations | Resource Consumption | Phase 2 Adoption Decision | Integration Strategy | Alternatives |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **libmagic** | [file/file](https://github.com/file/file) | Canonical C library and magic database for file identification | BSD-2-Clause | Highly active (v5.46 maintained) | Native C runtime (`libmagic.so`) | Linux, macOS, Windows (via Cygwin/vcpkg) | Extensive (>10,000 file types across OSes) | Can misclassify text files as generic `text/plain`; may confuse modern OOXML with generic `application/zip` | Very low (~1-2ms per file, ~5MB RAM) | **Adopt as primary C layer** | Bundled via OS packages (`libmagic1`) and wrapped by `python-magic`. | pure Python magic scanners |
| **python-magic** | [ahupp/python-magic](https://github.com/ahupp/python-magic) | Python ctypes binding for `libmagic` | MIT | Active | `libmagic` C library | All platforms with `libmagic` installed | Matches `libmagic` system database | Requires native C library installed on host/container | Lightweight (<1MB Python footprint) | **Adopt for Phase 2** | Primary detection layer wrapped inside `MagicDetector`, with fallback to built-in pure Python signatures if libmagic is missing. | `filetype`, `puremagic` |
| **Apache Tika** | [apache/tika](https://github.com/apache/tika) | Content analysis toolkit & MIME detector | Apache-2.0 | Active (v2.9+) | Java 11+ runtime | Cross-platform (JVM) | Extremely broad (>1,500 legacy and modern formats) | Requires Java JVM; heavyweight process startup; high memory footprint (~200MB+ JVM heap) | High (JVM overhead, 50-150ms per file) | **Do not integrate in Phase 2** | Evaluated but rejected for Phase 2 detection. Adding JVM for file detection violates modular lightweight principles. May be containerized in Phase 3 if legacy binary office parsing is needed. | `python-magic` + custom heuristics |
| **TrID** | [mark0.net/soft-trid-e.html](https://mark0.net/soft-trid-e.html) | Signature-based file identifier with ~15,000 XML signature definitions | Freeware (Closed source binary) | Sporadic / slow | Proprietary x86 binary / DLL | Windows, Linux x86 binary | Very large signature database | **Closed source**, binary only; licensing prohibits redistribution or enterprise modifications; requires external subprocess execution | Moderate (external binary execution per file) | **Rejected** | Cannot be integrated due to closed-source licensing, proprietary binary requirements, and security risks of executing third-party binaries. | Open-source signature database (`libmagic`, PRONOM, Gary Kessler signatures) |

### Key Detection Strategy for Phase 2:
1. **Multi-Signal Architecture:** No single tool is trusted. A 7-step pipeline combines:
   - File system validity checks (size, permissions, non-special)
   - Extension parsing (canonicalization, case-insensitivity)
   - Built-in binary magic byte signature scanning (independent of external libraries)
   - `python-magic` / `libmagic` MIME type determination
   - Deep container structure inspection (OOXML, OpenDocument, EPUB with strict safety limits)
   - Text format structural heuristics (JSON, XML, YAML, CSV, Markdown, Code syntax)
   - Multi-signal cross-validation (detecting extension mismatches, polyglots, and corruption)
2. **Defensive Safety Limits:** Container and archive inspection strictly enforce 1MB decompression limits, max 100 entries read, max depth 2, and zero code execution.
