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


class ExtractionStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    PASSWORD_REQUIRED = "password_required"
    CANCELLED = "cancelled"


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    CODE = "code"
    EQUATION = "equation"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    IMAGE_REFERENCE = "image_reference"
    UNKNOWN = "unknown"


__all__ = [
    "AIMode",
    "BatchStatus",
    "BlockType",
    "ExtractionStatus",
    "FileStatus",
    "FormatCategory",
    "JobStatus",
]
