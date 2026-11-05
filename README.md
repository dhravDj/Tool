# DocuMind AI

**Universal File Intelligence Platform**

DocuMind AI is a scalable, modular platform designed to accept, identify, extract, understand, structure, and convert content from a wide spectrum of file formats—ranging from PDFs, office spreadsheets, presentations, and technical diagrams to audio, video, source code, and scientific literature.

---

## 1. System Highlights & Architecture

DocuMind AI is engineered as a **Modular Monolith** with strict Clean Architecture separation, prepared to process batches of **10,000+ files** while offering complete data sovereignty through local-first AI inference.

```
Frontend (React 19 + TypeScript + Vite)
    │
    ▼
FastAPI API Gateway Layer (/api/v1)
    │
    ├── Request ID & Correlation Logging
    ├── Zero-Trust Input & Path Sanitization
    └── Centralized Error Handling & Envelopes
    │
Application Layer (Bounded Contexts)
    ├── File Management & Storage Hierarchy
    ├── Format Detection & MIME Registry
    ├── Processing Orchestrator & Batch State Machine
    ├── Extensible Plugin & Extraction Adapter Registry
    ├── AI Provider Registry (Local-First Default)
    └── Structured Output & Export Engine
    │
Infrastructure & Persistence Layer
    ├── PostgreSQL 16 (UUID primary keys, ACID state, JSONB metadata)
    ├── Redis 7 (In-memory caching and durable queue broker)
    ├── Local Storage Adapter (Partitioned filesystem scratchpads)
    └── Object Storage Adapter (MinIO / AWS S3 ready)
```

For complete architectural specifications, see [ARCHITECTURE.md](file:///home/dhanrraj/Documents/c/ARCHITECTURE.md) and [TECHNICAL_DECISIONS.md](file:///home/dhanrraj/Documents/c/TECHNICAL_DECISIONS.md).

---

## 2. Prerequisites

- **Linux / macOS / Windows (WSL2)**
- **Python 3.12+** (tested on Python 3.13)
- **Node.js v20+** (tested on Node v26) and **npm**
- **Docker & Docker Compose v2+** (for PostgreSQL and Redis)
- **uv** (recommended for ultra-fast Python package management)

---

## 3. Quick Start & Installation

### Option A: Automated Setup (Recommended)

Run the included setup script to configure both backend and frontend environments:

```bash
./scripts/setup.sh
```

### Option B: Manual Setup

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```

2. **Backend Setup:**
   ```bash
   uv venv --python 3.13 .venv
   source .venv/bin/activate
   uv pip install -e "backend[dev]"
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start Database & Cache Infrastructure:**
   ```bash
   docker compose up -d postgres redis
   ```

5. **Run Database Migrations:**
   ```bash
   ./scripts/migrate.sh
   ```

---

## 4. Running the Platform

### Running with Docker Compose (Full Stack)
```bash
./scripts/start.sh docker
```
- **Web Dashboard:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Gateway:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Running in Local Development Mode
```bash
./scripts/start.sh local
```

### Stopping Services
```bash
./scripts/stop.sh
```

---

## 5. Running the Test & Quality Suite

DocuMind AI maintains comprehensive testing and static analysis across backend and frontend:

```bash
./scripts/run_tests.sh
```

This single command executes:
1. **Python Linter & Formatter (`Ruff`):** Enforces code style and clean imports.
2. **Static Type Checker (`mypy`):** Strict static typing across all backend modules.
3. **Backend Tests (`pytest`):** Unit and integration tests for API endpoints, plugin registry, security routines, database models, and error handling.
4. **Frontend Type Check (`tsc --noEmit`):** Validates all TypeScript types and JSX components.
5. **Frontend Tests (`Vitest` + `React Testing Library`):** Tests component rendering, modal dialogs, status indicators, and routing.

---

## 6. Project Directory Structure

```
DocuMind-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST endpoints (health, plugins, system, files, batches)
│   │   ├── core/                # Config, logging, security, exceptions
│   │   ├── domain/              # Enums, schemas, and clean domain entities
│   │   ├── infrastructure/      # SQLAlchemy models, async session, storage adapters
│   │   ├── plugins/             # Plugin interfaces, registry, and mock adapters
│   │   └── main.py              # Application factory and lifespan manager
│   ├── migrations/              # Alembic database migration scripts
│   ├── tests/                   # Pytest unit and integration test suite
│   ├── pyproject.toml           # Backend build, dependencies, ruff, mypy, pytest config
│   └── alembic.ini              # Database migration configuration
├── frontend/
│   ├── src/
│   │   ├── app/                 # Root App and routing configuration
│   │   ├── components/ui/       # Accessible UI components (StatCard, EmptyState, etc.)
│   │   ├── layouts/             # MainLayout, Sidebar, Header
│   │   ├── pages/               # Dashboard, Upload, Jobs, Library, Settings, Status
│   │   ├── services/            # Typed API client
│   │   └── stores/              # Zustand UI state store (theme, sidebar)
│   ├── tests/                   # Vitest unit and component tests
│   ├── package.json             # Frontend dependencies and scripts
│   └── vite.config.ts           # Vite and Vitest configuration
├── infrastructure/
│   ├── docker/                  # Multi-stage production Dockerfiles
│   └── monitoring/              # System health and diagnostic configs
├── storage/                     # Partitioned local storage (uploads, temporary, processed)
├── scripts/                     # Operational bash scripts (setup, start, stop, migrate, test)
├── .env.example                 # Comprehensive environment variable template
├── docker-compose.yml           # Multi-container orchestration (PG, Redis, Backend, Frontend)
├── ARCHITECTURE.md              # System design and scaling specification
├── DEVELOPMENT_PROGRESS.md      # Progress tracker and milestone checklist
├── ENVIRONMENT_REPORT.md        # Host hardware, driver, and tool report
├── OPEN_SOURCE_ECOSYSTEM.md     # In-depth open-source candidate evaluations
├── SECURITY.md                  # Security controls and threat modeling
└── TECHNICAL_DECISIONS.md       # Architecture Decision Records (ADRs)
```

---

## 7. Security Foundation

DocuMind AI implements **Defense in Depth**:
- **Zero-Trust Upload Validation:** File names are strictly sanitized to prevent path traversal (`../../`). Magic byte signatures are verified against registered extensions.
- **No Direct Code Execution:** Uploaded files are strictly treated as data and isolated in restricted scratchpads (`storage/temporary/`).
- **Data Sovereignty:** AI processing defaults to local execution (`AI_MODE=local`, `LOCAL_MODEL_PROVIDER=ollama`). Cloud processing is disabled by default and requires explicit administrator opt-in and user consent.
- **Sanitized Error Responses:** Internal database columns and stack traces are never exposed to API consumers; all errors include unique request correlation IDs.

For further details, consult [SECURITY.md](file:///home/dhanrraj/Documents/c/SECURITY.md).

---

## 8. Development Roadmap

- [x] **Phase 1: Foundation, Architecture & Engineering Setup** (Completed)
- [ ] **Phase 2: Universal File Detection & Ingestion Engine** (Next)
- [ ] **Phase 3: Deep Document & Layout Extraction** (PDF, Office, Scans)
- [ ] **Phase 4: Multimodal Extraction** (Audio, Video, Images, Code, Archives)
- [ ] **Phase 5: Local & Cloud AI Enrichment** (Summarization, Entity Extraction, Q&A)
- [ ] **Phase 6: Universal Output, Export & Search** (Markdown, JSON, Parquet, Vector RAG)
