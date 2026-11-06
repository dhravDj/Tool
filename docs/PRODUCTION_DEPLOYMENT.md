# DocuMind AI — Production Deployment Guide

## 1. Deployment Topology Overview

DocuMind AI supports two production deployment topologies depending on throughput, compliance, and infrastructure footprint requirements:

### Topology A: Single-Host Sovereign Appliance (Edge / SME / Air-Gapped)
- **Deployment Unit:** Single bare-metal server or VM orchestrating Docker Compose.
- **Components:**
  - `nginx-edge`: Reverse proxy, SSL/TLS termination, rate limiting (20 rps per IP, burst 50), HTTP security headers, static SPA caching.
  - `documind-api`: FastAPI application running Uvicorn ASGI workers behind Gunicorn.
  - `documind-worker`: Celery / Python background processing workers consuming from priority task queue.
  - `documind-postgres`: PostgreSQL 16 with pgvector extension enabled for persistent canonical storage and vector embeddings.
  - `documind-redis`: Redis 7 running in append-only persistence mode (`appendonly yes`) for task broker and distributed caching.
- **Recommended Hardware Sizing:**
  - CPU: 8+ vCPU (x86_64 or ARM64)
  - Memory: 16 GB - 32 GB ECC RAM
  - Storage: 200 GB+ NVMe SSD (fast I/O for extraction and keyframe storage)
  - GPU: Optional (NVIDIA T4 / A10G for accelerated Whisper/OCR inference; sovereign CPU fallback active by default).

### Topology B: High-Throughput Scalable Distributed Cluster (Enterprise / Cloud)
- **Deployment Unit:** Managed Kubernetes (GKE / EKS / AKS) or distributed VM fleet.
- **Components:**
  - Cloud Ingress Controller / ALB with TLS termination and WAF.
  - Horizontally scaled API pods (`min: 3, max: 20`) with HPA based on CPU / request latency.
  - Dedicated worker pools partitioned by task tier:
    - *Interactive Pool:* High-priority, small documents, latency < 1.5s.
    - *Standard Document Pool:* PDF, Office, Spreadsheets, Code, Archives.
    - *Heavy Multimodal Pool:* Audio diarization, video scene analysis, frame OCR.
  - Managed PostgreSQL 16 (Google Cloud SQL / AWS RDS Aurora) with Multi-AZ replication.
  - Managed Redis Cluster (Google Cloud Memorystore / AWS ElastiCache) with in-transit encryption and AUTH.
  - Object Storage: S3 / Google Cloud Storage for persistent raw files, keyframes, and extraction artifacts with lifecycle retention policies.

---

## 2. Container Architecture & Docker Compose Setup

The platform uses `docker-compose.prod.yml` configured for zero-trust production execution:

```bash
# 1. Clone repository on production host
git clone https://github.com/dhanrraj/c.git /opt/documind
cd /opt/documind

# 2. Configure production secrets
cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production

# 3. Pull / Build production images
docker compose -f docker-compose.prod.yml build

# 4. Launch containers in background
docker compose -f docker-compose.prod.yml up -d

# 5. Verify container health status
docker compose -f docker-compose.prod.yml ps
```

### Container Resource Limits Configuration
Each container in `docker-compose.prod.yml` enforces memory and CPU limits to prevent noisy neighbors and out-of-memory cascading faults:
- `backend`: `cpus: '4.0'`, `memory: 8192M`, reservation: `2048M`
- `postgres`: `cpus: '2.0'`, `memory: 4096M`, reservation: `1024M`
- `redis`: `cpus: '1.0'`, `memory: 2048M`, reservation: `512M`
- `nginx`: `cpus: '1.0'`, `memory: 512M`, reservation: `128M`

---

## 3. Reverse Proxy & Edge Ingress (Nginx)

The production Nginx edge configuration (`infrastructure/docker/nginx.prod.conf`) provides:
1. **Rate Limiting:** `limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;` with burst capacity of 50 requests.
2. **Buffer Overflow & Size Protections:**
   - `client_max_body_size 500M;` (accommodates high-resolution video and archive uploads).
   - `client_body_buffer_size 1M;`
3. **HTTP Security Headers:**
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
4. **Gzip Compression:** Accelerated transfer for text, JSON, SVG, CSS, and JS.
5. **SPA Routing:** `try_files $uri $uri/ /index.html;` ensures seamless HTML5 client-side navigation.

---

## 4. SSL/TLS Certificate Provisioning

For public internet deployments, configure Let's Encrypt automated renewal with Certbot:

```bash
# Install certbot
apt-get update && apt-get install -y certbot python3-certbot-nginx

# Obtain and install certificate
certbot certonly --standalone -d documind.example.com --email ops@example.com --agree-tos --no-eff-email

# Mount certificates into nginx container in docker-compose.prod.yml:
# - /etc/letsencrypt/live/documind.example.com/fullchain.pem:/etc/nginx/ssl/live.crt:ro
# - /etc/letsencrypt/live/documind.example.com/privkey.pem:/etc/nginx/ssl/live.key:ro
```

---

## 5. Production Health Verification

Verify full stack operation using native health endpoints:

```bash
# Check platform health
curl -s http://localhost/api/v1/health | jq .

# Response:
# {
#   "status": "healthy",
#   "timestamp": "2026-11-07T00:50:00Z",
#   "services": {
#     "database": "connected",
#     "redis": "connected",
#     "storage": "writable"
#   }
# }
```
