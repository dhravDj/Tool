"""Defensive security validator and quota tracker for archive operations."""

import re
import time
from pathlib import Path

from app.modules.archive_intelligence.config import ArchiveSafetyConfig, archive_config


class ArchiveIntelligenceError(Exception):
    """Base exception for archive intelligence operations."""


class PathTraversalError(ArchiveIntelligenceError):
    """Raised when an entry path attempts directory traversal or link escape."""


class SymlinkSecurityError(ArchiveIntelligenceError):
    """Raised when a symlink attempts to point outside the extraction sandbox."""


class SpecialFileSecurityError(ArchiveIntelligenceError):
    """Raised when encountering dangerous special files (device nodes, FIFOs, sockets)."""


class ArchiveBombError(ArchiveIntelligenceError):
    """Raised when decompression exceeds compression ratio or size limits."""


class ArchiveQuotaExceededError(ArchiveIntelligenceError):
    """Raised when extraction exceeds total size or entry count quotas."""


class ArchiveTimeoutError(ArchiveIntelligenceError):
    """Raised when extraction duration exceeds time budget."""


class ArchiveEncryptedError(ArchiveIntelligenceError):
    """Raised when password-protected archive cannot be decrypted."""

    def __init__(self, message: str, is_unsupported: bool = False) -> None:
        super().__init__(message)
        self.is_unsupported = is_unsupported


class ArchiveCorruptedError(ArchiveIntelligenceError):
    """Raised when archive header or stream structure is corrupted."""


class PathSecurityValidator:
    """Validates and normalizes entry paths to prevent path traversal and escapes."""

    WINDOWS_DRIVE_PATTERN = re.compile(r"^[a-zA-Z]:")
    UNC_PATTERN = re.compile(r"^[/\\]{2}")
    ENCODED_TRAVERSAL_PATTERN = re.compile(r"(%2e|%2f|%5c)", re.IGNORECASE)

    @classmethod
    def sanitize_and_normalize(
        cls,
        raw_path: str,
        dest_root: Path,
        max_path_length: int = 1024,
    ) -> tuple[Path, str, list[str]]:
        """Validate an archive entry path and compute a safe destination path inside dest_root.

        Returns (resolved_destination_path, normalized_relative_path, warnings).
        Raises PathTraversalError if traversal cannot be safely neutralized.
        """
        warnings: list[str] = []

        if not raw_path:
            raise PathTraversalError("Empty entry path")

        # Reject null bytes
        if "\0" in raw_path:
            raise PathTraversalError(f"Null byte detected in entry path: {raw_path!r}")

        # Check encoded traversal attempts
        if cls.ENCODED_TRAVERSAL_PATTERN.search(raw_path):
            warnings.append(f"Encoded traversal sequence detected in path: {raw_path}")

        # Check absolute path
        if raw_path.startswith(("/", "\\")):
            raise PathTraversalError(f"Absolute path traversal detected: {raw_path}")

        # Normalize slashes
        clean = raw_path.replace("\\", "/")

        # Check Windows drive or UNC
        if cls.WINDOWS_DRIVE_PATTERN.match(clean):
            raise PathTraversalError(f"Windows drive path detected: {raw_path}")

        if cls.UNC_PATTERN.match(clean):
            raise PathTraversalError(f"UNC network path blocked: {raw_path}")

        # Check for explicit traversal components
        parts = clean.split("/")
        safe_parts: list[str] = []
        for part in parts:
            if part in ("", "."):
                continue
            if part == "..":
                # Traversal attempt!
                raise PathTraversalError(
                    f"Directory traversal component '..' detected in path: {raw_path}"
                )
            safe_parts.append(part)

        if not safe_parts:
            # Entry resolved to root directory
            normalized_rel = "."
        else:
            normalized_rel = "/".join(safe_parts)

        if len(normalized_rel) > max_path_length:
            raise PathTraversalError(
                f"Path length {len(normalized_rel)} exceeds maximum limit {max_path_length}"
            )

        # Resolve against destination root
        dest_root_resolved = dest_root.resolve()
        candidate = (dest_root_resolved / normalized_rel).resolve()

        # Strict containment verification
        try:
            candidate.relative_to(dest_root_resolved)
        except ValueError as err:
            raise PathTraversalError(
                f"Resolved path '{candidate}' escapes destination root '{dest_root_resolved}'"
            ) from err

        return candidate, normalized_rel, warnings


class ExtractionQuotaTracker:
    """Stateful tracker for streaming resource limits and archive bomb protection."""

    def __init__(self, config: ArchiveSafetyConfig | None = None) -> None:
        self.config = config or archive_config
        self.start_time = time.monotonic()
        self.total_entries = 0
        self.total_decompressed_bytes = 0
        self.current_file_bytes = 0
        self.warnings: list[str] = []

    def start_new_file(self) -> None:
        """Reset single-file byte counter."""
        self.current_file_bytes = 0

    def record_entry(self) -> None:
        """Increment entry count and check limits."""
        self.total_entries += 1
        if self.total_entries > self.config.max_entries_per_archive:
            raise ArchiveQuotaExceededError(
                f"Archive entry count limit ({self.config.max_entries_per_archive}) exceeded"
            )
        if self.total_entries > self.config.max_total_entries_per_job:
            raise ArchiveQuotaExceededError(
                f"Job total entry count limit ({self.config.max_total_entries_per_job}) exceeded"
            )

    def record_chunk(self, chunk_len: int, compressed_entry_size: int = 0) -> None:
        """Record streamed chunk and verify decompression limits and compression ratios."""
        self.current_file_bytes += chunk_len
        self.total_decompressed_bytes += chunk_len

        # Check timeout
        self.check_timeout()

        # Check single file size limit
        if self.current_file_bytes > self.config.max_single_file_size_bytes:
            raise ArchiveBombError(
                f"Single extracted file size ({self.current_file_bytes} bytes) exceeds limit "
                f"({self.config.max_single_file_size_bytes} bytes)"
            )

        # Check total job size limit
        if self.total_decompressed_bytes > self.config.max_total_extracted_size_bytes:
            raise ArchiveQuotaExceededError(
                f"Total extracted size ({self.total_decompressed_bytes} bytes) exceeds limit "
                f"({self.config.max_total_extracted_size_bytes} bytes)"
            )

        # Compression ratio / bomb heuristic
        if self.current_file_bytes > 5 * 1024 * 1024 and compressed_entry_size > 0:
            effective_comp = max(compressed_entry_size, 1024)
            ratio = self.current_file_bytes / effective_comp
            if ratio > self.config.max_compression_ratio:
                raise ArchiveBombError(
                    f"Suspicious compression ratio ({ratio:.1f}:1) exceeds limit "
                    f"({self.config.max_compression_ratio:.1f}:1) for file of {self.current_file_bytes} bytes"
                )

    def check_timeout(self) -> None:
        """Ensure execution time has not exceeded budget."""
        elapsed = time.monotonic() - self.start_time
        if elapsed > self.config.max_extraction_time_seconds:
            raise ArchiveTimeoutError(
                f"Extraction timed out after {elapsed:.1f}s (budget: {self.config.max_extraction_time_seconds}s)"
            )
