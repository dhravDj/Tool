"""Health check and telemetry schemas."""

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    status: str = Field(description="ok | degraded | error | not_configured")
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, str] | None = None


class HealthCheckResponse(BaseModel):
    """Detailed system health check combining liveness and readiness."""

    status: str = Field(description="healthy | degraded | unhealthy")
    version: str
    environment: str
    uptime_seconds: float
    database: ComponentHealth
    redis: ComponentHealth
    storage: ComponentHealth
    ai_engine: ComponentHealth


class LivenessResponse(BaseModel):
    """Minimal liveness probe for container orchestration."""

    status: str = "alive"
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe indicating if the service is ready to accept traffic."""

    ready: bool
    status: str
    checks: dict[str, str]
