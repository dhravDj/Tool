"""Safe inspector for 7-Zip format archives."""

import hashlib
from pathlib import Path
from typing import Any

import py7zr

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


class SevenZipInspector(BaseArchiveInspector):
    """Safely inspects 7-Zip archives without full decompression."""

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
            "format": "7z",
            "file_size": file_size,
            "comment": None,
            "is_encrypted": False,
            "is_corrupted": False,
        }

        archive_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:8]

        try:
            with py7zr.SevenZipFile(file_path, mode="r") as sz:
                needs_pw = sz.needs_password()
                metadata["is_encrypted"] = needs_pw
                if needs_pw:
                    safety.encryption_detected = True
                    safety.warnings.append("Archive has password-protected entries.")

                file_infos = sz.list()
                metadata["raw_entry_count"] = len(file_infos)

                if len(file_infos) > max_entries:
                    safety.entry_limit_exceeded = True
                    safety.warnings.append(
                        f"Entry count {len(file_infos)} exceeds limit {max_entries}; capping inspection."
                    )
                    file_infos = file_infos[:max_entries]

                total_uncompressed = 0
                total_compressed = 0
                dir_count = 0
                file_count = 0
                nested_count = 0

                for idx, info in enumerate(file_infos):
                    raw_name = info.filename
                    is_dir = info.is_directory
                    is_sym = getattr(info, "is_symlink", False)

                    if is_sym:
                        safety.symlink_entries_blocked += 1
                        safety.warnings.append(f"Symlink detected in 7z archive: {raw_name}")

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

                    u_size = info.uncompressed or 0
                    c_size = info.compressed or 0

                    # Bomb heuristic
                    if c_size > 0 and (u_size / c_size > 100):
                        safety.compression_ratio_exceeded = True
                        safety.suspicious_entries += 1
                        safety.warnings.append(
                            f"Suspicious compression ratio on '{raw_name}': {u_size}/{c_size}"
                        )

                    is_nested = is_nested_archive_path(filename) if not is_dir else False
                    if is_nested:
                        nested_count += 1

                    if is_dir:
                        dir_count += 1
                    else:
                        file_count += 1
                        total_uncompressed += u_size
                        total_compressed += c_size

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
                        entry_type="directory" if is_dir else ("symlink" if is_sym else "file"),
                        compressed_size=c_size,
                        uncompressed_size=u_size,
                        compression_method="lzma2/7z",
                        checksum=f"{info.crc32:08x}" if info.crc32 else None,
                        encrypted=needs_pw,
                        is_directory=is_dir,
                        is_symlink=is_sym,
                        is_nested_archive=is_nested,
                        detection_result=detection,
                        processing_status="inspected",
                    )
                    entries.append(entry)

                metadata["total_uncompressed_size"] = total_uncompressed
                metadata["total_compressed_size"] = total_compressed or file_size
                metadata["compression_ratio"] = (
                    round(total_uncompressed / (total_compressed or file_size), 2)
                    if (total_compressed or file_size) > 0
                    else 1.0
                )
                metadata["directory_count"] = dir_count
                metadata["file_count"] = file_count
                metadata["nested_archive_count"] = nested_count
                metadata["encrypted_entry_count"] = len(file_infos) if needs_pw else 0

        except py7zr.exceptions.PasswordRequired:
            metadata["is_encrypted"] = True
            safety.encryption_detected = True
            safety.warnings.append("7-Zip archive is password-protected; header encrypted.")
        except py7zr.exceptions.Bad7zFile as err:
            metadata["is_corrupted"] = True
            safety.corruption_detected = True
            safety.warnings.append(f"Corrupted 7-Zip archive: {err}")
        except Exception as err:
            metadata["is_corrupted"] = True
            safety.warnings.append(f"Error inspecting 7-Zip archive: {err}")

        return metadata, entries, safety
