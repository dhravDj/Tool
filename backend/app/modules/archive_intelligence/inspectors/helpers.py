"""Helper functions for archive inspection and entry format classification."""

import hashlib
from pathlib import Path
from typing import Any

from app.modules.formats.registry import format_registry

NESTED_ARCHIVE_EXTENSIONS = {"zip", "7z", "tar", "gz", "tgz", "bz2", "tbz2", "tbz", "xz", "txz"}

NESTED_COMPOUND_EXTENSIONS = {"tar.gz", "tar.bz2", "tar.xz"}


def is_nested_archive_path(filename: str) -> bool:
    """Determine whether a path represents a nested archive container."""
    name_lower = filename.lower().strip()
    for compound in NESTED_COMPOUND_EXTENSIONS:
        if name_lower.endswith(f".{compound}"):
            return True
    ext = Path(name_lower).suffix.lstrip(".")
    return ext in NESTED_ARCHIVE_EXTENSIONS


def classify_entry_format(filename: str) -> dict[str, Any]:
    """Classify format, MIME, and category based on filename extension."""
    name_lower = filename.lower().strip()
    matched_fmt = None

    for compound in NESTED_COMPOUND_EXTENSIONS:
        if name_lower.endswith(f".{compound}"):
            matched = format_registry.get_by_extension(compound.split(".")[-1])
            if matched:
                matched_fmt = matched[0]
                break

    if not matched_fmt:
        ext = Path(name_lower).suffix.lstrip(".")
        if ext:
            matched = format_registry.get_by_extension(ext)
            if matched:
                matched_fmt = matched[0]

    if matched_fmt:
        return {
            "format_id": matched_fmt.format_id,
            "canonical_name": matched_fmt.canonical_name,
            "category": matched_fmt.category.value,
            "mime_type": matched_fmt.primary_mime,
            "confidence": 0.85,
        }

    return {
        "format_id": "unknown",
        "canonical_name": "Generic Binary / Unknown",
        "category": "unknown",
        "mime_type": "application/octet-stream",
        "confidence": 0.20,
    }


def compute_entry_id(archive_hash: str, raw_path: str, index: int) -> str:
    """Generate deterministic, collision-free entry identifier."""
    token = f"{archive_hash}:{index}:{raw_path}"
    return hashlib.sha256(token.encode("utf-8", errors="replace")).hexdigest()[:16]
