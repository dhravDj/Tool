"""Pydantic schemas for batch management and tracking in DocuMind AI (Phase 12)."""

from typing import Any

from pydantic import BaseModel, Field


class ProcessingPolicy(BaseModel):
    """Configuration governing pipeline stages, concurrency, and error tolerance."""

    pipeline_stages: list[str] = Field(
        default=["detection", "extraction", "ai_indexing"],
        description="Stages to execute: detection, extraction, ai_indexing, embedding",
    )
    max_concurrency: int = Field(
        default=4, ge=1, le=32, description="Max concurrent files processed within this batch"
    )
    error_tolerance: str = Field(
        default="continue_on_error",
        description="continue_on_error | halt_on_error | threshold_percentage",
    )
    error_threshold_percent: float = Field(
        default=25.0, ge=0.0, le=100.0, description="Halt batch if failed files exceed this %"
    )
    priority: int = Field(
        default=30, ge=1, le=100, description="Task queue priority (10=maintenance, 30=bulk, 50=normal, 80=interactive)"
    )
    ocr_enabled: bool = Field(default=True, description="Enable OCR for scanned images/PDFs")
    ai_indexing_enabled: bool = Field(default=True, description="Automatically index into Phase 11 KnowledgeBase")
    auto_start: bool = Field(default=True, description="Start batch automatically upon creation/upload")


class BatchCreateRequest(BaseModel):
    """Payload to create a new empty processing batch."""

    name: str = Field(..., min_length=1, max_length=255, description="Human-readable batch label")
    policy: ProcessingPolicy = Field(default_factory=ProcessingPolicy, description="Execution policy")


class BatchFileItem(BaseModel):
    """Individual file representation inside a batch."""

    id: str = Field(..., description="BatchFile UUID")
    file_id: str | None = Field(default=None, description="Persisted FileRecord UUID if registered")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(default=0, description="File size in bytes")
    sha256: str | None = Field(default=None, description="SHA256 checksum")
    status: str = Field(..., description="accepted, rejected, queued, processing, completed, partially_completed, failed, cancelled")
    validation_error: str | None = Field(default=None, description="Validation or rejection reason")
    dedup_decision: str | None = Field(default=None, description="new, reused, skipped")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class ProcessingBatchResponse(BaseModel):
    """Complete status, counts, and metrics for a processing batch."""

    id: str = Field(..., description="Batch UUID")
    name: str = Field(..., description="Batch name")
    status: str = Field(..., description="pending, queued, processing, paused, completed, partially_completed, failed, cancelled")
    total_files: int = Field(default=0)
    accepted_files: int = Field(default=0)
    rejected_files: int = Field(default=0)
    queued_files: int = Field(default=0)
    processing_files: int = Field(default=0)
    completed_files: int = Field(default=0)
    partially_completed_files: int = Field(default=0)
    failed_files: int = Field(default=0)
    cancelled_files: int = Field(default=0)
    total_size_bytes: int = Field(default=0)
    overall_progress: float = Field(default=0.0, description="Percentage (0.0 to 100.0)")
    processing_policy: dict[str, Any] = Field(default_factory=dict)
    error_summary: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    updated_at: str


class BatchProgressResponse(BaseModel):
    """Lightweight progress payload for polling or SSE updates."""

    batch_id: str
    status: str
    overall_progress: float
    total_files: int
    completed_files: int
    failed_files: int
    processing_files: int
    queued_files: int
    elapsed_seconds: float | None = None
    estimated_remaining_seconds: float | None = None
    current_throughput_files_per_sec: float | None = None


class BatchReportResponse(BaseModel):
    """Comprehensive exportable audit report for a finished batch."""

    batch_id: str
    name: str
    status: str
    summary_metrics: dict[str, Any]
    policy: dict[str, Any]
    files: list[BatchFileItem]
    errors: list[dict[str, Any]]
    execution_timeline: dict[str, Any]
    exported_at: str
