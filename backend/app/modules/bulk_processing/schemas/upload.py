"""Pydantic schemas for multi-file streaming bulk uploads."""

from pydantic import BaseModel, Field


class BulkUploadItemResult(BaseModel):
    """Validation and registration outcome for a single file in a bulk submission."""

    filename: str
    status: str = Field(..., description="accepted, rejected, reused")
    file_id: str | None = None
    batch_file_id: str | None = None
    file_size: int = 0
    sha256: str | None = None
    format_id: str | None = None
    error_message: str | None = None
    dedup_decision: str = "new"  # new | reused | skipped


class BulkUploadManifestResponse(BaseModel):
    """Overall batch manifest returned after multipart streaming upload."""

    batch_id: str
    batch_name: str
    total_submitted: int
    total_accepted: int
    total_rejected: int
    total_reused: int
    total_size_bytes: int
    files: list[BulkUploadItemResult]
    auto_started: bool = False
    manifest_generated_at: str


class BulkUploadConfig(BaseModel):
    """Configurable system upload thresholds and constraints."""

    max_files_per_batch: int = 10000
    max_batch_size_bytes: int = 10 * 1024 * 1024 * 1024  # 10 GB
    max_individual_file_size_bytes: int = 500 * 1024 * 1024  # 500 MB
    max_concurrent_uploads: int = 8
    max_upload_duration_seconds: int = 1800  # 30 minutes
