"""Archive inspector registry and format dispatcher."""

from pathlib import Path
from typing import Any

from app.modules.archive_intelligence.inspectors.base import BaseArchiveInspector
from app.modules.archive_intelligence.inspectors.gzip_inspector import GzipInspector
from app.modules.archive_intelligence.inspectors.sevenzip_inspector import SevenZipInspector
from app.modules.archive_intelligence.inspectors.tar_inspector import TarInspector
from app.modules.archive_intelligence.inspectors.zip_inspector import ZipInspector
from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveEntry,
    ArchiveSafetyReport,
)


class ArchiveInspectorRegistry:
    """Detects format and dispatches to appropriate safe archive inspector."""

    def __init__(self) -> None:
        self.zip_inspector = ZipInspector()
        self.tar_inspector = TarInspector()
        self.sevenzip_inspector = SevenZipInspector()
        self.gzip_inspector = GzipInspector()

    def get_inspector(
        self, file_path: Path, claimed_format: str | None = None
    ) -> BaseArchiveInspector:
        """Select inspector by header magic bytes, claimed format, or extension."""
        file_path = Path(file_path)
        fmt = (claimed_format or "").lower().strip()

        # 1. Read first 16 bytes for magic signature dispatch
        magic = b""
        try:
            with open(file_path, "rb") as f:
                magic = f.read(16)
        except Exception:
            pass

        # Check Zip: PK\x03\x04 or PK\x05\x06
        if magic.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            return self.zip_inspector

        # Check 7-Zip: 7z\xbc\xaf'\x1c
        if magic.startswith(b"7z\xbc\xaf\x27\x1c"):
            return self.sevenzip_inspector

        # Check Bzip2
        if magic.startswith(b"BZh"):
            return self.tar_inspector

        # Check XZ
        if magic.startswith(b"\xfd7zXZ\x00"):
            return self.tar_inspector

        # Check Gzip: \x1f\x8b
        if magic.startswith(b"\x1f\x8b"):
            # Check if it's a tar.gz or standalone gz
            name_lower = file_path.name.lower()
            if name_lower.endswith((".tar.gz", ".tgz")):
                return self.tar_inspector
            # Try tar inspection first, if it fails, fallback to gzip
            try:
                import tarfile

                if tarfile.is_tarfile(file_path):
                    return self.tar_inspector
            except Exception:
                pass
            return self.gzip_inspector

        # Check Tar: ustar at offset 257
        try:
            with open(file_path, "rb") as f:
                f.seek(257)
                ustar = f.read(5)
                if ustar == b"ustar":
                    return self.tar_inspector
        except Exception:
            pass

        # Fallback by extension
        name_lower = file_path.name.lower()
        if name_lower.endswith(".zip") or fmt == "zip":
            return self.zip_inspector
        if name_lower.endswith(".7z") or fmt == "7z":
            return self.sevenzip_inspector
        if name_lower.endswith(
            (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tbz", ".tar.xz", ".txz")
        ) or fmt in ("tar", "tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz", "txz"):
            return self.tar_inspector
        if name_lower.endswith(".gz") or fmt == "gz":
            return self.gzip_inspector

        # Default fallback to zip
        return self.zip_inspector

    def inspect(
        self,
        file_path: Path,
        claimed_format: str | None = None,
        max_entries: int = 10000,
    ) -> tuple[dict[str, Any], list[ArchiveEntry], ArchiveSafetyReport]:
        """Inspect archive safely using matching inspector."""
        file_path = Path(file_path)
        inspector = self.get_inspector(file_path, claimed_format)
        return inspector.inspect(file_path, max_entries=max_entries)


inspector_registry = ArchiveInspectorRegistry()
