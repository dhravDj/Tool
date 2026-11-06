"""Pydantic schemas for job scheduling, worker heartbeats, and system capacity telemetry."""

from typing import Any

from pydantic import BaseModel, Field


class JobAttemptResponse(BaseModel):
    """Detailed audit attempt record."""

    id: str
    attempt_number: int
    worker_id: str
    status: str
    started_at: str
    finished_at: str | None = None
    error_message: str | None = None
    duration_ms: float | None = None
    memory_peak_mb: float | None = None


class JobResponse(BaseModel):
    """Detailed job status and progress model."""

    id: str
    batch_id: str | None = None
    batch_file_id: str | None = None
    file_id: str
    filename: str | None = None
    job_type: str
    stage: str
    priority: int
    status: str
    current_worker_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    progress: float = 0.0
    stage_progress: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str
    error_code: str | None = None
    error_message: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


class QueueStatusResponse(BaseModel):
    """Real-time queue depth and backlog metrics."""

    queues: dict[str, int] = Field(
        default_factory=dict,
        description="Depth per queue (interactive, normal, bulk, maintenance)",
    )
    total_queued: int = 0
    total_processing: int = 0
    total_dead_letter: int = 0
    avg_latency_ms: float = 0.0
    active_workers_count: int = 0
    timestamp: str


class WorkerStatusResponse(BaseModel):
    """Telemetry for an active worker node."""

    worker_id: str
    hostname: str
    pid: int
    worker_type: str
    current_job_id: str | None = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    gpu_utilization: float | None = None
    gpu_memory_used_mb: float | None = None
    status: str  # alive, idle, busy, shutting_down, dead
    last_heartbeat: str
    started_at: str


class SystemCapacityResponse(BaseModel):
    """Overall system ingestion, queue, extraction, and AI processing capacity."""

    host_info: dict[str, Any]
    max_parallel_cpu_workers: int
    max_concurrent_gpu_slots: int
    active_cpu_slots_in_use: int
    active_gpu_slots_in_use: int
    submission_capacity_files_per_sec: float
    detection_capacity_files_per_sec: float
    extraction_capacity_files_per_sec: float
    ai_indexing_capacity_chunks_per_sec: float
    is_under_backpressure: bool
    backpressure_reason: str | None = None
    evaluated_at: str


class ResourceUsageResponse(BaseModel):
    """Live host hardware resource readings."""

    cpu: dict[str, Any]
    memory: dict[str, Any]
    gpu: dict[str, Any]
    storage: dict[str, Any]
    timestamp: str
