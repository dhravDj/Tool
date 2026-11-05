"""Health check endpoints supporting liveness, readiness, and subsystem diagnostics."""

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.health import (
    ComponentHealth,
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.infrastructure.database.session import check_database_connectivity
from app.infrastructure.queue.redis import redis_manager
from app.infrastructure.storage.local import local_storage

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])

# Record service start timestamp
START_TIME = time.time()


@router.get("", response_model=APIResponse[HealthCheckResponse])
async def full_health_check(response: Response) -> APIResponse[HealthCheckResponse]:
    """Inspect full application health including database, cache, storage, and AI engine."""
    # 1. Check Database
    db_ok, db_latency, db_msg = await check_database_connectivity()
    db_health = ComponentHealth(
        status="ok" if db_ok else "error",
        latency_ms=db_latency,
        message=db_msg,
    )

    # 2. Check Redis
    redis_ok, redis_latency, redis_msg = await redis_manager.check_connectivity()
    redis_health = ComponentHealth(
        status="ok" if redis_ok else "degraded",
        latency_ms=redis_latency,
        message=redis_msg,
    )

    # 3. Check Storage
    storage_start = time.perf_counter()
    storage_ok = await local_storage.check_health()
    storage_latency = (time.perf_counter() - storage_start) * 1000
    storage_health = ComponentHealth(
        status="ok" if storage_ok else "error",
        latency_ms=round(storage_latency, 2),
        message=f"Storage backend: {settings.STORAGE_BACKEND} (root: {settings.STORAGE_LOCAL_ROOT})",
        details={"writable": str(storage_ok)},
    )

    # 4. Check AI Engine Configuration
    ai_health = ComponentHealth(
        status="ok",
        message=f"Mode: {settings.AI_MODE}, Provider: {settings.LOCAL_MODEL_PROVIDER}, Device: {settings.LOCAL_INFERENCE_DEVICE}",
        details={
            "ai_mode": settings.AI_MODE,
            "local_provider": settings.LOCAL_MODEL_PROVIDER,
            "device": settings.LOCAL_INFERENCE_DEVICE,
            "cloud_enabled": str(settings.CLOUD_PROCESSING_ENABLED),
        },
    )

    # Determine overall status
    is_healthy = db_ok and storage_ok
    overall_status = (
        "healthy" if (is_healthy and redis_ok) else ("degraded" if is_healthy else "unhealthy")
    )

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    health_data = HealthCheckResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        uptime_seconds=round(time.time() - START_TIME, 2),
        database=db_health,
        redis=redis_health,
        storage=storage_health,
        ai_engine=ai_health,
    )

    return APIResponse.ok(
        data=health_data,
        message=f"DocuMind AI status: {overall_status}",
    )


@router.get("/liveness", response_model=LivenessResponse)
async def liveness_probe() -> LivenessResponse:
    """Minimal liveness probe for Kubernetes and Docker container monitoring."""
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_probe(response: Response) -> ReadinessResponse:
    """Readiness probe indicating if the service can receive user requests."""
    db_ok, _, _ = await check_database_connectivity()
    storage_ok = await local_storage.check_health()
    ready = db_ok and storage_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=ready,
        status="ready" if ready else "not_ready",
        checks={
            "database": "ok" if db_ok else "unreachable",
            "storage": "ok" if storage_ok else "unwritable",
        },
    )
