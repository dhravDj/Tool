"""Base interface for safe archive inspectors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveEntry,
    ArchiveSafetyReport,
)


class BaseArchiveInspector(ABC):
    """Abstract archive inspector extracting metadata and entry list without full decompression."""

    @abstractmethod
    def inspect(
        self,
        file_path: Path,
        max_entries: int = 10000,
    ) -> tuple[dict[str, Any], list[ArchiveEntry], ArchiveSafetyReport]:
        """Safely inspect archive and return (metadata, entries, safety_report)."""
        pass
