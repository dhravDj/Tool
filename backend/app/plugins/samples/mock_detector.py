"""Sample mock detector plugin demonstrating interface implementation."""

from pathlib import Path
from typing import Any

from app.domain.enums import FormatCategory
from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.detector import DetectionResult, FileDetectorInterface


class MockTextDetectorPlugin(FileDetectorInterface):
    """Sample detector verifying plain text and markdown format detection."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="mock_text_detector",
            version="1.0.0",
            description="Phase 1 sample detector for plain text and markdown files.",
            plugin_type=PluginType.DETECTOR,
            supported_formats=["txt", "text/plain", "md", "text/markdown"],
            required_dependencies=[],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        return True

    async def detect(
        self,
        file_path: Path,
        original_filename: str | None = None,
    ) -> DetectionResult:
        suffix = file_path.suffix.lower().lstrip(".")
        if suffix in ("txt", "text"):
            return DetectionResult(
                mime_type="text/plain",
                extension="txt",
                category=FormatCategory.DOCUMENT,
                confidence=0.95,
                detected_by=self.metadata.name,
                encoding="utf-8",
            )
        elif suffix in ("md", "markdown"):
            return DetectionResult(
                mime_type="text/markdown",
                extension="md",
                category=FormatCategory.DOCUMENT,
                confidence=0.95,
                detected_by=self.metadata.name,
                encoding="utf-8",
            )

        return DetectionResult(
            mime_type="application/octet-stream",
            extension=suffix or "bin",
            category=FormatCategory.UNKNOWN,
            confidence=0.1,
            detected_by=self.metadata.name,
        )
