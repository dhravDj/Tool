# DocuMind AI — Production Configuration & Environment Guide

## 1. Environment Variable Reference

The platform reads configuration from environment variables defined in `.env.production`:

| Variable | Required | Default | Description | Example |
|---|---|---|---|---|
| `ENVIRONMENT` | Yes | `production` | Runtime mode (`production`, `development`, `testing`) | `production` |
| `DEBUG` | No | `False` | Disables debug endpoints and enables strict HSTS | `False` |
| `SECRET_KEY` | Yes | - | Cryptographic key for JWT token signing (>= 32 bytes) | `e1b7c... (openssl rand -hex 32)` |
| `DATABASE_URL` | Yes | - | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `DATABASE_POOL_SIZE` | No | `20` | SQLAlchemy connection pool size | `30` |
| `DATABASE_MAX_OVERFLOW` | No | `10` | Maximum pool overflow connections | `20` |
| `REDIS_URL` | Yes | - | Redis connection URL for priority queue and cache | `redis://:password@host:6379/0` |
| `STORAGE_BASE_DIR` | No | `./storage` | Base directory for file storage | `/var/lib/documind/storage` |
| `CORS_ORIGINS` | Yes | - | JSON list of allowed web origins | `["https://documind.example.com"]` |
| `MAX_UPLOAD_SIZE_MB` | No | `500` | Global maximum upload limit per file in MB | `500` |
| `WORKER_CONCURRENCY` | No | `4` | Number of concurrent tasks per worker process | `8` |
| `GEMINI_API_KEY` | No | - | Optional Google Gemini API key for external LLM | `AIzaSy...` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Optional local Ollama server address | `http://ollama:11434` |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## 2. Generating Strong Secrets

Always generate cryptographic keys using secure entropy sources:

```bash
# Generate SECRET_KEY (32 bytes hex)
openssl rand -hex 32

# Generate Redis AUTH password
openssl rand -base64 24

# Generate PostgreSQL password
openssl rand -base64 24
```

---

## 3. Database Connection Pool Sizing

Tune database connection pools to match your expected concurrency and available PostgreSQL resources:

$$\text{Total Connections} = (\text{Backend Replicas} \times (\text{DATABASE\_POOL\_SIZE} + \text{DATABASE\_MAX\_OVERFLOW})) + \text{Worker Connections} + \text{Reserved (10)}$$

For a 2-replica API deployment with `DATABASE_POOL_SIZE=20` and `DATABASE_MAX_OVERFLOW=10`:
$$\text{Peak Connections} = (2 \times (20 + 10)) + 10 + 10 = 80 \text{ connections}$$
Ensure `max_connections` in `postgresql.conf` is configured to at least 150.
