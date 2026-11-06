# DocuMind AI — Continuous Integration & Continuous Deployment (CI/CD)

## 1. Overview & Quality Gates

The DocuMind AI repository uses GitHub Actions (`.github/workflows/ci.yml`) to enforce rigorous quality gates on every Pull Request and commit to the `main` branch.

```
[Git Push / PR]
       │
       ├──► [Backend Quality Gates]
       │        ├── ruff format & lint check
       │        └── pytest test suite (264+ tests)
       │
       └──► [Frontend Quality Gates]
                ├── TypeScript compilation check (tsc -b)
                ├── Vitest test suite (16 suites, 28 tests)
                └── Production bundle build (vite build)
```

---

## 2. GitHub Actions Workflow Configuration

Located at `.github/workflows/ci.yml`:

```yaml
name: DocuMind AI CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-quality-gate:
    name: Backend Lint, Typing & Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: documind
          POSTGRES_PASSWORD: documind_test_password
          POSTGRES_DB: documind_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg libmagic1 libgl1-mesa-glx

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip uv
          uv pip install --system -r backend/requirements.txt
          uv pip install --system ruff pytest pytest-asyncio

      - name: Run Ruff Linter
        run: ruff check backend/

      - name: Run Pytest Test Suite
        env:
          DATABASE_URL: postgresql+asyncpg://documind:documind_test_password@localhost:5432/documind_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest backend/tests/

  frontend-quality-gate:
    name: Frontend Typecheck, Tests & Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm --prefix frontend ci

      - name: Run TypeScript Typecheck
        run: npm --prefix frontend run build -- --noEmit

      - name: Run Vitest Unit & Integration Tests
        run: npm --prefix frontend test -- --run

      - name: Build Production Frontend Bundle
        run: npm --prefix frontend run build
```

---

## 3. Branch Protection & Release Promotion

- **Protected Branch:** `main` requires all CI checks to pass before merging.
- **Automated Rollback Strategy:**
  - Production deployments use Docker image tags corresponding to Git commit SHA (`documind-api:${{ github.sha }}`).
  - In the event of health check failure or post-deployment anomaly, rolling back to the previous stable release requires updating the image tag and executing `docker compose up -d`.
