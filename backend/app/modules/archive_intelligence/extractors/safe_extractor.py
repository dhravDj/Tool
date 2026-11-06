"""Safe isolated streaming extraction engine with path traversal and archive bomb defenses."""

import gzip
import hashlib
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import py7zr

from app.modules.archive_intelligence.config import ArchiveSafetyConfig, archive_config
from app.modules.archive_intelligence.inspectors.helpers import (
    compute_entry_id,
    is_nested_archive_path,
)
from app.modules.archive_intelligence.inspectors.registry import inspector_registry
from app.modules.archive_intelligence.safety import (
    ArchiveBombError,
    ArchiveEncryptedError,
    ArchiveQuotaExceededError,
    ArchiveTimeoutError,
    ExtractionQuotaTracker,
    PathSecurityValidator,
    PathTraversalError,
)
from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveEntry,
    ArchiveSafetyReport,
)


class SafeArchiveExtractor:
    """Extracts archives into isolated directories enforcing path validation and resource quotas."""

    def __init__(self, config: ArchiveSafetyConfig | None = None) -> None:
        self.config = config or archive_config

    def extract(
        self,
        file_path: Path,
        dest_root: Path,
        selected_entry_ids: list[str] | None = None,
        password: str | None = None,
    ) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], ArchiveSafetyReport
    ]:
        """Safely extract archive entries into dest_root.

        Returns (extracted_files, blocked_entries, failed_entries, safety_report).
        """
        dest_root.mkdir(parents=True, exist_ok=True)
        tracker = ExtractionQuotaTracker(self.config)
        safety = ArchiveSafetyReport()

        extracted_files: list[dict[str, Any]] = []
        blocked_entries: list[dict[str, Any]] = []
        failed_entries: list[dict[str, Any]] = []

        # 1. Run safe inspection first
        metadata, entries, insp_safety = inspector_registry.inspect(
            file_path=file_path,
            max_entries=self.config.max_entries_per_archive,
        )

        # Merge inspection safety into report
        safety.path_traversal_blocked = insp_safety.path_traversal_blocked
        safety.symlink_entries_blocked = insp_safety.symlink_entries_blocked
        safety.suspicious_entries = insp_safety.suspicious_entries
        safety.size_limit_exceeded = insp_safety.size_limit_exceeded
        safety.compression_ratio_exceeded = insp_safety.compression_ratio_exceeded
        safety.entry_limit_exceeded = insp_safety.entry_limit_exceeded
        safety.encryption_detected = insp_safety.encryption_detected
        safety.corruption_detected = insp_safety.corruption_detected
        safety.blocked_entry_count = insp_safety.blocked_entry_count
        safety.warnings.extend(insp_safety.warnings)

        if metadata.get("is_corrupted") and not entries:
            safety.corruption_detected = True
            return extracted_files, blocked_entries, failed_entries, safety

        # Filter entries if selective
        if selected_entry_ids is not None:
            selected_set = set(selected_entry_ids)
            target_entries = [e for e in entries if e.entry_id in selected_set]
        else:
            target_entries = entries

        # Track written filesystem paths to prevent collision overwrites
        written_paths: dict[Path, str] = {}

        archive_format = metadata.get("format", "zip")

        try:
            if archive_format == "zip":
                self._extract_zip(
                    file_path=file_path,
                    dest_root=dest_root,
                    entries=target_entries,
                    password=password,
                    tracker=tracker,
                    safety=safety,
                    extracted_files=extracted_files,
                    blocked_entries=blocked_entries,
                    failed_entries=failed_entries,
                    written_paths=written_paths,
                )
            elif archive_format in ("tar", "tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz", "txz"):
                self._extract_tar(
                    file_path=file_path,
                    dest_root=dest_root,
                    entries=target_entries,
                    tracker=tracker,
                    safety=safety,
                    extracted_files=extracted_files,
                    blocked_entries=blocked_entries,
                    failed_entries=failed_entries,
                    written_paths=written_paths,
                )
            elif archive_format == "7z":
                self._extract_7z(
                    file_path=file_path,
                    dest_root=dest_root,
                    entries=target_entries,
                    password=password,
                    tracker=tracker,
                    safety=safety,
                    extracted_files=extracted_files,
                    blocked_entries=blocked_entries,
                    failed_entries=failed_entries,
                    written_paths=written_paths,
                )
            elif archive_format == "gz":
                self._extract_gz(
                    file_path=file_path,
                    dest_root=dest_root,
                    entries=target_entries,
                    tracker=tracker,
                    safety=safety,
                    extracted_files=extracted_files,
                    blocked_entries=blocked_entries,
                    failed_entries=failed_entries,
                    written_paths=written_paths,
                )
            else:
                safety.warnings.append(
                    f"Unsupported archive format for extraction: {archive_format}"
                )

        except ArchiveBombError as err:
            safety.compression_ratio_exceeded = True
            safety.size_limit_exceeded = True
            safety.warnings.append(f"Archive bomb limit triggered: {err}")
        except ArchiveQuotaExceededError as err:
            safety.size_limit_exceeded = True
            safety.entry_limit_exceeded = True
            safety.warnings.append(f"Quota exceeded: {err}")
        except ArchiveTimeoutError as err:
            safety.timeout_exceeded = True
            safety.warnings.append(f"Extraction timed out: {err}")
        except ArchiveEncryptedError as err:
            safety.encryption_detected = True
            safety.warnings.append(f"Archive encryption error: {err}")
        except Exception as err:
            safety.warnings.append(f"Extraction exception encountered: {err}")

        return extracted_files, blocked_entries, failed_entries, safety

    def _resolve_unique_dest(
        self,
        raw_path: str,
        dest_root: Path,
        written_paths: dict[Path, str],
        entry_id: str,
    ) -> Path:
        """Resolve a safe destination path, disambiguating collisions to prevent overwrites."""
        target, norm_rel, _ = PathSecurityValidator.sanitize_and_normalize(
            raw_path, dest_root, max_path_length=self.config.max_path_length
        )

        if target in written_paths and written_paths[target] != entry_id:
            # Collision! Disambiguate by appending entry ID prefix before extension
            parent = target.parent
            stem = target.stem
            suffix = target.suffix
            disambiguated = parent / f"{stem}_{entry_id[:8]}{suffix}"
            target = disambiguated

        written_paths[target] = entry_id
        return target

    def _extract_zip(
        self,
        file_path: Path,
        dest_root: Path,
        entries: list[ArchiveEntry],
        password: str | None,
        tracker: ExtractionQuotaTracker,
        safety: ArchiveSafetyReport,
        extracted_files: list[dict[str, Any]],
        blocked_entries: list[dict[str, Any]],
        failed_entries: list[dict[str, Any]],
        written_paths: dict[Path, str],
    ) -> None:
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                if password:
                    zf.setpassword(password.encode())

                for entry in entries:
                    if entry.is_directory:
                        continue

                    # Validate path traversal
                    try:
                        target = self._resolve_unique_dest(
                            entry.original_path, dest_root, written_paths, entry.entry_id
                        )
                    except PathTraversalError as err:
                        safety.path_traversal_blocked += 1
                        safety.blocked_entry_count += 1
                        safety.warnings.append(str(err))
                        blocked_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "reason": f"Path traversal: {err}",
                                "status": "blocked",
                            }
                        )
                        continue

                    target.parent.mkdir(parents=True, exist_ok=True)
                    tracker.record_entry()
                    tracker.start_new_file()

                    hasher = hashlib.sha256()
                    bytes_written = 0

                    try:
                        with zf.open(entry.original_path) as src, open(target, "wb") as dst:
                            while True:
                                chunk = src.read(self.config.chunk_size_bytes)
                                if not chunk:
                                    break
                                tracker.record_chunk(len(chunk), entry.compressed_size)
                                hasher.update(chunk)
                                dst.write(chunk)
                                bytes_written += len(chunk)

                        extracted_files.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "normalized_path": str(target.relative_to(dest_root)),
                                "extracted_path": str(target),
                                "file_size": bytes_written,
                                "sha256": hasher.hexdigest(),
                                "is_nested_archive": entry.is_nested_archive,
                                "status": "extracted",
                            }
                        )

                    except RuntimeError as err:
                        # Clean up partial file
                        if target.exists():
                            target.unlink(missing_ok=True)
                        err_str = str(err).lower()
                        if "password" in err_str or "encrypted" in err_str:
                            safety.encryption_detected = True
                            failed_entries.append(
                                {
                                    "entry_id": entry.entry_id,
                                    "original_path": entry.original_path,
                                    "error": "PASSWORD_REQUIRED",
                                    "status": "failed",
                                }
                            )
                        else:
                            failed_entries.append(
                                {
                                    "entry_id": entry.entry_id,
                                    "original_path": entry.original_path,
                                    "error": str(err),
                                    "status": "failed",
                                }
                            )
                    except Exception as err:
                        if target.exists():
                            target.unlink(missing_ok=True)
                        if isinstance(
                            err, (ArchiveBombError, ArchiveQuotaExceededError, ArchiveTimeoutError)
                        ):
                            raise
                        failed_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "error": str(err),
                                "status": "failed",
                            }
                        )

        except zipfile.BadZipFile as err:
            safety.corruption_detected = True
            safety.warnings.append(f"Bad zip file: {err}")

    def _extract_tar(
        self,
        file_path: Path,
        dest_root: Path,
        entries: list[ArchiveEntry],
        tracker: ExtractionQuotaTracker,
        safety: ArchiveSafetyReport,
        extracted_files: list[dict[str, Any]],
        blocked_entries: list[dict[str, Any]],
        failed_entries: list[dict[str, Any]],
        written_paths: dict[Path, str],
    ) -> None:
        try:
            with tarfile.open(file_path, "r:*") as tf:
                # Build lookup of members by name
                member_map = {m.name: m for m in tf.getmembers()}

                for entry in entries:
                    if entry.is_directory:
                        continue

                    member = member_map.get(entry.original_path)
                    if not member:
                        continue

                    # Reject symlinks and special files
                    if member.issym() or member.islnk():
                        safety.symlink_entries_blocked += 1
                        safety.blocked_entry_count += 1
                        blocked_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "reason": f"Symlink or hardlink blocked: {entry.original_path}",
                                "status": "blocked",
                            }
                        )
                        continue

                    if member.isdev() or member.isfifo() or member.ischr() or member.isblk():
                        safety.suspicious_entries += 1
                        safety.blocked_entry_count += 1
                        blocked_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "reason": f"Special device file blocked: {entry.original_path}",
                                "status": "blocked",
                            }
                        )
                        continue

                    # Validate path traversal
                    try:
                        target = self._resolve_unique_dest(
                            entry.original_path, dest_root, written_paths, entry.entry_id
                        )
                    except PathTraversalError as err:
                        safety.path_traversal_blocked += 1
                        safety.blocked_entry_count += 1
                        safety.warnings.append(str(err))
                        blocked_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "reason": f"Path traversal: {err}",
                                "status": "blocked",
                            }
                        )
                        continue

                    target.parent.mkdir(parents=True, exist_ok=True)
                    tracker.record_entry()
                    tracker.start_new_file()

                    hasher = hashlib.sha256()
                    bytes_written = 0

                    try:
                        src = tf.extractfile(member)
                        if src is None:
                            continue

                        with src, open(target, "wb") as dst:
                            while True:
                                chunk = src.read(self.config.chunk_size_bytes)
                                if not chunk:
                                    break
                                tracker.record_chunk(len(chunk), entry.compressed_size)
                                hasher.update(chunk)
                                dst.write(chunk)
                                bytes_written += len(chunk)

                        extracted_files.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "normalized_path": str(target.relative_to(dest_root)),
                                "extracted_path": str(target),
                                "file_size": bytes_written,
                                "sha256": hasher.hexdigest(),
                                "is_nested_archive": entry.is_nested_archive,
                                "status": "extracted",
                            }
                        )

                    except Exception as err:
                        if target.exists():
                            target.unlink(missing_ok=True)
                        if isinstance(
                            err, (ArchiveBombError, ArchiveQuotaExceededError, ArchiveTimeoutError)
                        ):
                            raise
                        failed_entries.append(
                            {
                                "entry_id": entry.entry_id,
                                "original_path": entry.original_path,
                                "error": str(err),
                                "status": "failed",
                            }
                        )

        except Exception as err:
            safety.corruption_detected = True
            safety.warnings.append(f"TAR reading error: {err}")

    def _extract_7z(
        self,
        file_path: Path,
        dest_root: Path,
        entries: list[ArchiveEntry],
        password: str | None,
        tracker: ExtractionQuotaTracker,
        safety: ArchiveSafetyReport,
        extracted_files: list[dict[str, Any]],
        blocked_entries: list[dict[str, Any]],
        failed_entries: list[dict[str, Any]],
        written_paths: dict[Path, str],
    ) -> None:
        # 7-Zip safe staging extraction
        staging_dir = dest_root / ".staging_7z"
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            with py7zr.SevenZipFile(file_path, mode="r", password=password) as sz:
                if sz.needs_password() and not password:
                    safety.encryption_detected = True
                    raise ArchiveEncryptedError("PASSWORD_REQUIRED")

                sz.extractall(path=staging_dir)

            # Move and validate extracted files
            entry_map = {e.original_path.replace("\\", "/"): e for e in entries}

            for staged_file in staging_dir.rglob("*"):
                if staged_file.is_dir():
                    continue

                rel_str = str(staged_file.relative_to(staging_dir)).replace("\\", "/")
                entry = entry_map.get(rel_str)
                entry_id = entry.entry_id if entry else compute_entry_id("7z", rel_str, 0)
                is_nested = entry.is_nested_archive if entry else is_nested_archive_path(rel_str)

                try:
                    target = self._resolve_unique_dest(rel_str, dest_root, written_paths, entry_id)
                except PathTraversalError as err:
                    safety.path_traversal_blocked += 1
                    safety.blocked_entry_count += 1
                    safety.warnings.append(str(err))
                    blocked_entries.append(
                        {
                            "entry_id": entry_id,
                            "original_path": rel_str,
                            "reason": f"Path traversal: {err}",
                            "status": "blocked",
                        }
                    )
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)
                tracker.record_entry()

                # Verify file size and compute sha256
                f_size = staged_file.stat().st_size
                tracker.record_chunk(f_size, 0)

                hasher = hashlib.sha256()
                with open(staged_file, "rb") as sf, open(target, "wb") as df:
                    while True:
                        buf = sf.read(self.config.chunk_size_bytes)
                        if not buf:
                            break
                        hasher.update(buf)
                        df.write(buf)

                extracted_files.append(
                    {
                        "entry_id": entry_id,
                        "original_path": rel_str,
                        "normalized_path": str(target.relative_to(dest_root)),
                        "extracted_path": str(target),
                        "file_size": f_size,
                        "sha256": hasher.hexdigest(),
                        "is_nested_archive": is_nested,
                        "status": "extracted",
                    }
                )

        except py7zr.exceptions.PasswordRequired:
            safety.encryption_detected = True
            for e in entries:
                failed_entries.append(
                    {
                        "entry_id": e.entry_id,
                        "original_path": e.original_path,
                        "error": "PASSWORD_REQUIRED",
                        "status": "failed",
                    }
                )
        except Exception as err:
            if isinstance(err, (ArchiveBombError, ArchiveQuotaExceededError, ArchiveTimeoutError)):
                raise
            safety.warnings.append(f"7z extraction error: {err}")
        finally:
            # Clean up staging directory
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

    def _extract_gz(
        self,
        file_path: Path,
        dest_root: Path,
        entries: list[ArchiveEntry],
        tracker: ExtractionQuotaTracker,
        safety: ArchiveSafetyReport,
        extracted_files: list[dict[str, Any]],
        blocked_entries: list[dict[str, Any]],
        failed_entries: list[dict[str, Any]],
        written_paths: dict[Path, str],
    ) -> None:
        if not entries:
            return
        entry = entries[0]

        try:
            target = self._resolve_unique_dest(
                entry.normalized_path, dest_root, written_paths, entry.entry_id
            )
        except PathTraversalError as err:
            safety.path_traversal_blocked += 1
            safety.blocked_entry_count += 1
            safety.warnings.append(str(err))
            blocked_entries.append(
                {
                    "entry_id": entry.entry_id,
                    "original_path": entry.original_path,
                    "reason": f"Path traversal: {err}",
                    "status": "blocked",
                }
            )
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        tracker.record_entry()
        tracker.start_new_file()

        hasher = hashlib.sha256()
        bytes_written = 0

        try:
            with gzip.open(file_path, "rb") as src, open(target, "wb") as dst:
                while True:
                    chunk = src.read(self.config.chunk_size_bytes)
                    if not chunk:
                        break
                    tracker.record_chunk(len(chunk), entry.compressed_size)
                    hasher.update(chunk)
                    dst.write(chunk)
                    bytes_written += len(chunk)

            extracted_files.append(
                {
                    "entry_id": entry.entry_id,
                    "original_path": entry.original_path,
                    "normalized_path": str(target.relative_to(dest_root)),
                    "extracted_path": str(target),
                    "file_size": bytes_written,
                    "sha256": hasher.hexdigest(),
                    "is_nested_archive": entry.is_nested_archive,
                    "status": "extracted",
                }
            )

        except Exception as err:
            if target.exists():
                target.unlink(missing_ok=True)
            if isinstance(err, (ArchiveBombError, ArchiveQuotaExceededError, ArchiveTimeoutError)):
                raise
            failed_entries.append(
                {
                    "entry_id": entry.entry_id,
                    "original_path": entry.original_path,
                    "error": str(err),
                    "status": "failed",
                }
            )


safe_extractor = SafeArchiveExtractor()
