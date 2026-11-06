"""Safe inspector for ZIP format archives."""

import hashlib
import zipfile
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

ZIP_COMPRESSION_METHODS = {
    zipfile.ZIP_STORED: "stored",
    zipfile.ZIP_DEFLATED: "deflate",
    zipfile.ZIP_BZIP2: "bzip2",
    zipfile.ZIP_LZMA: "lzma",
}


class ZipInspector(BaseArchiveInspector):
    """Safely inspects standard and encrypted ZIP archives."""

    def inspect(
        self,
        file_path: Path,
        max_entries: int = 10000,
    ) -> tuple[dict[str, Any], list[ArchiveEntry], ArchiveSafetyReport]:
        file_path = Path(file_path)
        safety = ArchiveSafetyReport()
        entries: list[ArchiveEntry] = []
        metadata: dict[str, Any] = {
            "format": "zip",
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "comment": None,
            "is_encrypted": False,
            "is_corrupted": False,
        }

        # Deterministic hash for entry ID generation
        archive_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:8]

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                if zf.comment:
                    metadata["comment"] = zf.comment.decode("utf-8", errors="replace")

                infolist = zf.infolist()
                metadata["raw_entry_count"] = len(infolist)

                if len(infolist) > max_entries:
                    safety.entry_limit_exceeded = True
                    safety.warnings.append(
                        f"Entry count {len(infolist)} exceeds limit {max_entries}; capping inspection."
                    )
                    infolist = infolist[:max_entries]

                total_uncompressed = 0
                total_compressed = 0
                dir_count = 0
                file_count = 0
                nested_count = 0
                encrypted_count = 0

                for idx, info in enumerate(infolist):
                    raw_name = info.filename
                    is_dir = info.is_dir()
                    is_enc = bool(info.flag_bits & 0x1)

                    if is_enc:
                        encrypted_count += 1
                        safety.encryption_detected = True

                    # Path traversal checks
                    clean = raw_name.replace("\\", "/")
                    if (
                        ".." in clean.split("/")
                        or clean.startswith("/")
                        or (len(clean) > 1 and clean[1] == ":")
                    ):
                        safety.path_traversal_blocked += 1
                        safety.blocked_entry_count += 1
                        safety.warnings.append(
                            f"Blocked path traversal attempt in entry: {raw_name}"
                        )

                    # Normalization
                    safe_parts = [p for p in clean.split("/") if p not in ("", ".", "..")]
                    norm_path = "/".join(safe_parts)
                    filename = safe_parts[-1] if safe_parts else ""
                    ext = Path(filename).suffix.lstrip(".").lower() if filename else ""

                    # Bomb heuristic
                    if info.compress_size > 0 and (info.file_size / info.compress_size > 100):
                        safety.compression_ratio_exceeded = True
                        safety.suspicious_entries += 1
                        safety.warnings.append(
                            f"Suspicious compression ratio on '{raw_name}': {info.file_size}/{info.compress_size}"
                        )

                    is_nested = is_nested_archive_path(filename) if not is_dir else False
                    if is_nested:
                        nested_count += 1

                    if is_dir:
                        dir_count += 1
                    else:
                        file_count += 1
                        total_uncompressed += info.file_size
                        total_compressed += info.compress_size

                    detection = (
                        classify_entry_format(filename)
                        if not is_dir
                        else {
                            "format_id": "dir",
                            "canonical_name": "Directory",
                            "category": "directory",
                            "mime_type": "inode/directory",
                            "confidence": 1.0,
                        }
                    )

                    entry = ArchiveEntry(
                        entry_id=compute_entry_id(archive_hash, raw_name, idx),
                        original_path=raw_name,
                        normalized_path=norm_path,
                        filename=filename,
                        extension=ext,
                        entry_type="directory" if is_dir else "file",
                        compressed_size=info.compress_size,
                        uncompressed_size=info.file_size,
                        compression_method=ZIP_COMPRESSION_METHODS.get(
                            info.compress_type, f"type_{info.compress_type}"
                        ),
                        checksum=f"{info.CRC:08x}" if info.CRC else None,
                        encrypted=is_enc,
                        is_directory=is_dir,
                        is_symlink=False,
                        is_nested_archive=is_nested,
                        detection_result=detection,
                        processing_status="inspected",
                    )
                    entries.append(entry)

                metadata["total_uncompressed_size"] = total_uncompressed
                metadata["total_compressed_size"] = total_compressed
                metadata["compression_ratio"] = (
                    round(total_uncompressed / total_compressed, 2) if total_compressed > 0 else 1.0
                )
                metadata["directory_count"] = dir_count
                metadata["file_count"] = file_count
                metadata["nested_archive_count"] = nested_count
                metadata["encrypted_entry_count"] = encrypted_count
                metadata["is_encrypted"] = encrypted_count > 0

        except zipfile.BadZipFile as err:
            metadata["is_corrupted"] = True
            safety.corruption_detected = True
            safety.warnings.append(f"Corrupted or truncated ZIP archive: {err}")
        except Exception as err:
            metadata["is_corrupted"] = True
            safety.warnings.append(f"Error inspecting ZIP archive: {err}")

        return metadata, entries, safety
