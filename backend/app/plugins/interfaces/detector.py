"""File format detection plugin interface."""

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.domain.enums import FormatCategory
from app.plugins.interfaces.base import ProcessingPluginInterface


@dataclass(frozen=True)
class DetectionResult:
    """Result of file format and MIME detection."""

    mime_type: str
    extension: str
    category: FormatCategory
    confidence: float  # 0.0 to 1.0
    detected_by: str
    encoding: str | None = None


class FileDetectorInterface(ProcessingPluginInterface):
    """Interface for plugins that identify file formats via headers, magic bytes, or structure."""

    @abstractmethod
    async def detect(
        self,
        file_path: Path,
        original_filename: str | None = None,
    ) -> DetectionResult:
        """Inspect file content on disk and return detected MIME type and format category."""
        pass
