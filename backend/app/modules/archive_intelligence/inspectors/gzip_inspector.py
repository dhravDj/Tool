"""Safe inspector for standalone GZIP compressed files."""

import hashlib
import struct
from pathlib import Path
from typing import Any

from app.modules.archive_intelligence.inspectors.base import BaseArchiveInspector
from app.modules.archive_intelligence.inspectors.helpers import (
    classify_entry_format,
    compute_entry_id,
    is_nested_archive_path,
)
from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveEntry,
    ArchiveSafetyReport,
)


class GzipInspector(BaseArchiveInspector):
    """Inspects single-stream GZIP archives without full stream decompression."""

    def inspect(
        self,
        file_path: Path,
        max_entries: int = 10000,
    ) -> tuple[dict[str, Any], list[ArchiveEntry], ArchiveSafetyReport]:
        file_path = Path(file_path)
        safety = ArchiveSafetyReport()
        entries: list[ArchiveEntry] = []
        file_size = file_path.stat().st_size if file_path.exists() else 0

        metadata: dict[str, Any] = {
            "format": "gz",
            "file_size": file_size,
            "comment": None,
            "is_encrypted": False,
            "is_corrupted": False,
        }

        archive_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:8]

        try:
            with open(file_path, "rb") as f:
                header = f.read(10)
                if len(header) < 10 or header[:2] != b"\x1f\x8b":
                    metadata["is_corrupted"] = True
                    safety.corruption_detected = True
                    safety.warnings.append("Invalid GZIP header bytes.")
                    return metadata, entries, safety

                flg = header[3]
                mtime_int = struct.unpack("<I", header[4:8])[0]
                if mtime_int > 0:
                    metadata["mtime"] = mtime_int

                # If FEXTRA
                if flg & 0x04:
                    xlen_bytes = f.read(2)
                    if len(xlen_bytes) == 2:
                        xlen = struct.unpack("<H", xlen_bytes)[0]
                        f.seek(xlen, 1)

                # If FNAME (original filename stored)
                orig_filename = None
                if flg & 0x08:
                    name_bytes = bytearray()
                    while True:
                        b = f.read(1)
                        if not b or b == b"\x00":
                            break
                        name_bytes.extend(b)
                    if name_bytes:
                        orig_filename = name_bytes.decode("utf-8", errors="replace")

                # If FCOMMENT
                if flg & 0x10:
                    comment_bytes = bytearray()
                    while True:
                        b = f.read(1)
                        if not b or b == b"\x00":
                            break
                        comment_bytes.extend(b)
                    if comment_bytes:
                        metadata["comment"] = comment_bytes.decode("utf-8", errors="replace")

                # Read uncompressed size from the last 4 bytes (ISIZE in RFC 1952)
                f.seek(max(0, file_size - 4))
                isize_bytes = f.read(4)
                uncompressed_size = (
                    struct.unpack("<I", isize_bytes)[0] if len(isize_bytes) == 4 else file_size
                )

            # Determine filename
            stem_name = file_path.name
            if stem_name.lower().endswith(".gz"):
                stem_name = stem_name[:-3]
            entry_filename = orig_filename or stem_name or "extracted_data"

            # Check traversal on header filename if present
            if orig_filename and (".." in orig_filename or orig_filename.startswith("/")):
                safety.path_traversal_blocked += 1
                safety.blocked_entry_count += 1
                safety.warnings.append(f"Path traversal in GZIP header filename: {orig_filename}")

            clean_filename = Path(entry_filename).name
            ext = Path(clean_filename).suffix.lstrip(".").lower()
            is_nested = is_nested_archive_path(clean_filename)

            detection = classify_entry_format(clean_filename)

            entry = ArchiveEntry(
                entry_id=compute_entry_id(archive_hash, clean_filename, 0),
                original_path=orig_filename or clean_filename,
                normalized_path=clean_filename,
                filename=clean_filename,
                extension=ext,
                entry_type="file",
                compressed_size=file_size,
                uncompressed_size=uncompressed_size,
                compression_method="deflate",
                checksum=None,
                encrypted=False,
                is_directory=False,
                is_symlink=False,
                is_nested_archive=is_nested,
                detection_result=detection,
                processing_status="inspected",
            )
            entries.append(entry)

            metadata["total_uncompressed_size"] = uncompressed_size
            metadata["total_compressed_size"] = file_size
            metadata["compression_ratio"] = (
                round(uncompressed_size / file_size, 2) if file_size > 0 else 1.0
            )
            metadata["directory_count"] = 0
            metadata["file_count"] = 1
            metadata["nested_archive_count"] = 1 if is_nested else 0
            metadata["raw_entry_count"] = 1

        except Exception as err:
            metadata["is_corrupted"] = True
            safety.corruption_detected = True
            safety.warnings.append(f"Error inspecting GZIP file: {err}")

        return metadata, entries, safety
