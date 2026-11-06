"""Safe inspector for TAR and compressed TAR archives (tar, tar.gz, tgz, tar.bz2, tbz2, tar.xz, txz)."""

import hashlib
import tarfile
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


class TarInspector(BaseArchiveInspector):
    """Safely inspects TAR and compressed TAR archives without full extraction."""

    def inspect(
        self,
        file_path: Path,
        max_entries: int = 10000,
    ) -> tuple[dict[str, Any], list[ArchiveEntry], ArchiveSafetyReport]:
        file_path = Path(file_path)
        safety = ArchiveSafetyReport()
        entries: list[ArchiveEntry] = []
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Infer compression from filename
        name_lower = file_path.name.lower()
        if name_lower.endswith((".tar.gz", ".tgz")):
            detected_format = "tar.gz"
            compression_algo = "gzip"
        elif name_lower.endswith((".tar.bz2", ".tbz2", ".tbz")):
            detected_format = "tar.bz2"
            compression_algo = "bzip2"
        elif name_lower.endswith((".tar.xz", ".txz")):
            detected_format = "tar.xz"
            compression_algo = "xz"
        else:
            detected_format = "tar"
            compression_algo = "none"

        metadata: dict[str, Any] = {
            "format": detected_format,
            "compression_algorithm": compression_algo,
            "file_size": file_size,
            "comment": None,
            "is_encrypted": False,
            "is_corrupted": False,
        }

        archive_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:8]

        try:
            with tarfile.open(file_path, "r:*") as tf:
                members = tf.getmembers()
                metadata["raw_entry_count"] = len(members)

                if len(members) > max_entries:
                    safety.entry_limit_exceeded = True
                    safety.warnings.append(
                        f"Entry count {len(members)} exceeds limit {max_entries}; capping inspection."
                    )
                    members = members[:max_entries]

                total_uncompressed = 0
                dir_count = 0
                file_count = 0
                nested_count = 0

                for idx, member in enumerate(members):
                    raw_name = member.name
                    is_dir = member.isdir()
                    is_sym = member.issym()
                    is_special = (
                        member.isdev() or member.isfifo() or member.ischr() or member.isblk()
                    )

                    if is_special:
                        safety.suspicious_entries += 1
                        safety.blocked_entry_count += 1
                        safety.warnings.append(f"Blocked dangerous special device file: {raw_name}")

                    if is_sym:
                        safety.symlink_entries_blocked += 1
                        safety.warnings.append(
                            f"Symlink detected pointing to '{member.linkname}': {raw_name}"
                        )

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

                    is_nested = is_nested_archive_path(filename) if not is_dir else False
                    if is_nested:
                        nested_count += 1

                    if is_dir:
                        dir_count += 1
                        entry_type = "directory"
                    elif is_sym:
                        entry_type = "symlink"
                    elif member.islnk():
                        entry_type = "hardlink"
                    elif is_special:
                        entry_type = "special"
                    else:
                        file_count += 1
                        total_uncompressed += member.size
                        entry_type = "file"

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
                        entry_type=entry_type,
                        compressed_size=0,  # In tar, compression is stream-level, not per-file
                        uncompressed_size=member.size,
                        compression_method=compression_algo,
                        checksum=None,
                        encrypted=False,
                        is_directory=is_dir,
                        is_symlink=is_sym,
                        is_nested_archive=is_nested,
                        detection_result=detection,
                        processing_status="inspected",
                    )
                    entries.append(entry)

                metadata["total_uncompressed_size"] = total_uncompressed
                metadata["total_compressed_size"] = file_size
                metadata["compression_ratio"] = (
                    round(total_uncompressed / file_size, 2) if file_size > 0 else 1.0
                )
                metadata["directory_count"] = dir_count
                metadata["file_count"] = file_count
                metadata["nested_archive_count"] = nested_count
                metadata["encrypted_entry_count"] = 0
                metadata["is_encrypted"] = False

        except (tarfile.ReadError, tarfile.CompressionError) as err:
            metadata["is_corrupted"] = True
            safety.corruption_detected = True
            safety.warnings.append(f"Corrupted or invalid TAR archive: {err}")
        except Exception as err:
            metadata["is_corrupted"] = True
            safety.warnings.append(f"Error inspecting TAR archive: {err}")

        return metadata, entries, safety
