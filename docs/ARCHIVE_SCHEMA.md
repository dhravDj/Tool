# DocuMind AI — Archive Canonical Schemas

## 1. Overview

The canonical schemas for Phase 10 provide strongly typed Pydantic models for archive metadata, entry inventory, hierarchy representations, safety reports, and provenance relationships.

Module Location: `backend/app/modules/archive_intelligence/schemas/archive_document.py`

---

## 2. Core Schemas

### `ArchiveEntry`

Represents an individual entry (file, directory, or symlink) inside an archive.

```python
class ArchiveEntry(BaseModel):
    entry_id: str                          # Deterministic ID: archive_hash:path:index
    original_path: str                     # Raw path stored inside archive
    normalized_path: str                   # Sanitized relative POSIX path
    filename: str                          # Basename of the file
    extension: str                         # File extension without dot
    entry_type: str                        # "file", "directory", "symlink", "special"
    compressed_size: int                   # Compressed bytes in archive
    uncompressed_size: int                 # Decompressed bytes
    compression_method: str                # e.g., "deflate", "lzma2", "bzip2"
    checksum: str | None = None            # CRC32 or header checksum
    encrypted: bool = False                # Whether this entry requires decryption
    is_directory: bool = False             # Directory indicator
    is_symlink: bool = False               # Symlink indicator
    is_nested_archive: bool = False        # Whether this entry is an archive itself
    detection_result: dict[str, Any] = {}  # Multi-signal format detection result
    extracted_file_id: str | None = None   # Database UUID of created FileRecord
    processing_status: str = "inspected"   # "inspected", "extracted", "blocked", "failed"
    error: str | None = None               # Failure or block reason
```

### `ArchiveHierarchyNode`

Hierarchical node for building interactive directory trees in the UI and ASCII visualizers.

```python
class ArchiveHierarchyNode(BaseModel):
    id: str                                # Node identifier
    name: str                              # Folder or file display name
    path: str                              # Relative POSIX path
    is_directory: bool = False
    is_nested_archive: bool = False
    entry_id: str | None = None
    children: list["ArchiveHierarchyNode"] = []
    file_count: int = 0
    total_size: int = 0
    warnings: list[str] = []
```

### `ArchiveSafetyReport`

Security audit verdict capturing potential vulnerabilities, quota violations, and blocked entries.

```python
class ArchiveSafetyReport(BaseModel):
    path_traversal_blocked: int = 0        # Count of blocked path traversal attempts
    symlink_entries_blocked: int = 0       # Count of blocked escaping symlinks
    suspicious_entries: int = 0            # Devices, FIFOs, sockets blocked
    size_limit_exceeded: bool = False      # Single file or total size limit tripped
    compression_ratio_exceeded: bool = False # ZIP bomb threshold tripped
    entry_limit_exceeded: bool = False     # Entry count limit tripped
    nesting_limit_exceeded: bool = False   # Nesting depth exceeded limit
    timeout_exceeded: bool = False         # Decompression timed out
    encryption_detected: bool = False      # Archive or entries are password-protected
    corruption_detected: bool = False      # Header corruption or truncated archive
    blocked_entry_count: int = 0           # Total count of quarantined entries
    warnings: list[str] = []               # Security notices and advisory warnings
```

### `ArchiveDocument`

The top-level canonical document returned by the archive pipeline and REST APIs.

```python
class ArchiveDocument(BaseModel):
    archive_id: str                        # Analysis ID
    source_file_id: str                    # Parent FileRecord UUID
    archive_format: str                    # "zip", "7z", "tar", "tar.gz", etc.
    metadata: dict[str, Any] = {}          # Header comments, volume count, solid flags
    entries: list[ArchiveEntry] = []       # Complete member manifest
    hierarchy: ArchiveHierarchyNode        # Root directory hierarchy
    nested_archives: list[dict[str, Any]] = [] # Child archives detected
    extracted_files: list[dict[str, Any]] = [] # Safely extracted child files
    blocked_entries: list[dict[str, Any]] = [] # Blocked malicious entries
    failed_entries: list[dict[str, Any]] = []  # Corrupted or unextractable entries
    processing_mode: str = "extract_and_analyze" # Mode A, B, C, or D
    processing_status: str = "completed"   # "completed", "failed", "password_required"
    extracted_size: int = 0                # Total bytes extracted to storage
    total_entry_count: int = 0             # Total archive entries
    nesting_depth: int = 0                 # Current archive recursion depth
    safety_report: ArchiveSafetyReport     # Complete security evaluation
    processing_metadata: dict[str, Any] = {} # Latency, timestamps, engine info
    warnings: list[str] = []
    errors: list[str] = []
```
