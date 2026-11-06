"""Canonical schemas for Archive & Nested File Processing Engine (Phase 10)."""

from typing import Any

from pydantic import BaseModel, Field


class ArchiveEntry(BaseModel):
    """Canonical metadata for a single item within an archive."""

    entry_id: str = Field(..., description="Unique entry identifier")
    original_path: str = Field(..., description="Raw path as recorded inside the archive container")
    normalized_path: str = Field(..., description="Normalized safe relative internal path")
    filename: str = Field(..., description="Base filename of the entry")
    extension: str = Field(default="", description="Lowercased file extension without leading dot")
    entry_type: str = Field(
        default="file",
        description="Entry type: file, directory, symlink, hardlink, special",
    )
    compressed_size: int = Field(default=0, description="Compressed size in bytes")
    uncompressed_size: int = Field(default=0, description="Uncompressed size in bytes")
    compression_method: str = Field(
        default="", description="Compression algorithm used (e.g. deflate, lzma)"
    )
    checksum: str | None = Field(
        default=None, description="CRC32, Adler32, or SHA256 checksum if available"
    )
    encrypted: bool = Field(
        default=False, description="Whether this entry is password-protected or encrypted"
    )
    is_directory: bool = Field(default=False, description="Whether entry is a directory")
    is_symlink: bool = Field(default=False, description="Whether entry is a symbolic link")
    is_nested_archive: bool = Field(default=False, description="Whether entry is itself an archive")
    detection_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Detected file format, MIME, and category",
    )
    extracted_file_id: str | None = Field(
        default=None,
        description="UUID of created FileRecord if extracted",
    )
    processing_status: str = Field(
        default="inspected",
        description="Status: inspected, extracted, analyzed, blocked, failed, skipped",
    )
    error: str | None = Field(default=None, description="Error message if processing failed")


class ArchiveHierarchyNode(BaseModel):
    """Recursive hierarchy tree node representing an archive folder structure."""

    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Directory or file name")
    path: str = Field(..., description="Full normalized path from archive root")
    is_directory: bool = Field(
        default=False, description="Whether this node represents a directory"
    )
    is_nested_archive: bool = Field(
        default=False, description="Whether this node represents a nested archive"
    )
    entry_id: str | None = Field(default=None, description="Linked ArchiveEntry entry_id if file")
    children: list["ArchiveHierarchyNode"] = Field(default_factory=list, description="Child nodes")
    file_count: int = Field(default=0, description="Total child files contained under this node")
    total_size: int = Field(default=0, description="Aggregate uncompressed bytes under this node")
    warnings: list[str] = Field(
        default_factory=list, description="Warnings (e.g., collisions, special paths)"
    )


class ArchiveSafetyReport(BaseModel):
    """Defensive security audit findings for archive processing."""

    path_traversal_blocked: int = Field(
        default=0, description="Count of path traversal attempts blocked"
    )
    symlink_entries_blocked: int = Field(
        default=0, description="Count of symlinks or link escapes blocked"
    )
    suspicious_entries: int = Field(
        default=0, description="Count of suspicious entries (special files, device nodes)"
    )
    size_limit_exceeded: bool = Field(
        default=False, description="Whether file or archive size limits were hit"
    )
    compression_ratio_exceeded: bool = Field(
        default=False, description="Whether archive bomb ratio limits were hit"
    )
    entry_limit_exceeded: bool = Field(
        default=False, description="Whether maximum entry limit was reached"
    )
    nesting_limit_exceeded: bool = Field(
        default=False, description="Whether nesting depth limit was exceeded"
    )
    timeout_exceeded: bool = Field(
        default=False, description="Whether execution timeout was exceeded"
    )
    encryption_detected: bool = Field(
        default=False, description="Whether password encryption was detected"
    )
    corruption_detected: bool = Field(
        default=False, description="Whether corruption or truncation was found"
    )
    blocked_entry_count: int = Field(default=0, description="Total number of blocked entries")
    warnings: list[str] = Field(
        default_factory=list, description="Security warnings and defense actions taken"
    )


class ArchiveRelationship(BaseModel):
    """Parent-child hierarchy and provenance link for extracted and nested files."""

    parent_archive_id: str = Field(..., description="ArchiveAnalysisRecord ID of the container")
    parent_entry_id: str = Field(..., description="Entry ID within parent archive")
    child_file_id: str = Field(..., description="Extracted FileRecord UUID")
    root_archive_id: str = Field(..., description="Root uploaded ArchiveAnalysisRecord UUID")
    nesting_depth: int = Field(default=1, description="Depth level in archive hierarchy")
    original_path: str = Field(..., description="Original path in archive container")


class ArchiveModelInfo(BaseModel):
    """Archive engine metadata and versioning."""

    engine_name: str = Field(default="documind-archive-engine")
    model_name: str = Field(default="documind-archive-v1")
    version: str = Field(default="1.0.0")
    supported_formats: list[str] = Field(
        default_factory=lambda: [
            "zip",
            "7z",
            "tar",
            "tar.gz",
            "tgz",
            "gz",
            "tar.bz2",
            "tbz2",
            "tar.xz",
            "txz",
        ]
    )


class ArchiveCapabilities(BaseModel):
    """Capabilities and configured safety thresholds of the Archive Intelligence Engine."""

    supported_formats: list[str]
    max_nesting_depth: int
    max_entries_per_archive: int
    max_total_entries_per_job: int
    max_single_file_size_bytes: int
    max_total_extracted_size_bytes: int
    max_archive_size_bytes: int
    max_path_length: int
    max_extraction_time_seconds: int
    max_concurrent_jobs: int
    features: list[str]


class ArchiveDocument(BaseModel):
    """Canonical representation of an analyzed archive package."""

    archive_id: str = Field(..., description="Unique archive analysis record UUID")
    source_file_id: str = Field(..., description="Associated FileRecord UUID")
    archive_format: str = Field(..., description="Detected format: zip, 7z, tar, gz, etc.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Archive-level metadata")
    entries: list[ArchiveEntry] = Field(
        default_factory=list, description="All entries found in archive"
    )
    hierarchy: ArchiveHierarchyNode = Field(..., description="Hierarchical tree representation")
    nested_archives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Nested archive documents or summaries",
    )
    extracted_files: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Records of successfully extracted child files",
    )
    blocked_entries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Entries blocked due to security policies or safety limits",
    )
    failed_entries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Entries that failed inspection or extraction with errors",
    )
    processing_mode: str = Field(
        default="inspect_only",
        description="Mode: inspect_only, extract_only, extract_and_analyze, selective",
    )
    processing_status: str = Field(
        default="completed",
        description="Status: completed, partial, blocked, failed, password_required, unsupported_encryption",
    )
    extracted_size: int = Field(default=0, description="Total bytes extracted to disk")
    total_entry_count: int = Field(default=0, description="Total count of all entries")
    nesting_depth: int = Field(default=0, description="Nesting depth of this archive (0 for root)")
    safety_report: ArchiveSafetyReport = Field(default_factory=ArchiveSafetyReport)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
