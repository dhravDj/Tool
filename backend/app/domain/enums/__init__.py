"""Domain Enums for DocuMind AI."""

from enum import Enum

from app.modules.formats.categories import FormatCategory


class FileStatus(str, Enum):
    PENDING = "pending"
    STORED = "stored"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"
    DELETED = "deleted"


class BatchStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIMode(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


__all__ = ["AIMode", "BatchStatus", "FileStatus", "FormatCategory", "JobStatus"]
