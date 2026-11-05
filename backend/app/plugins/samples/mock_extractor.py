"""Sample mock extraction engine plugin demonstrating extraction interface."""

import time
from pathlib import Path
from typing import Any

from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.extractor import (
    ExtractedElement,
    ExtractionEngineInterface,
    ExtractionResult,
)


class MockTextExtractorPlugin(ExtractionEngineInterface):
    """Sample extractor verifying plain text document parsing interface compliance."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="mock_text_extractor",
            version="1.0.0",
            description="Phase 1 sample extractor for plain text files (verifies interface compliance).",
            plugin_type=PluginType.EXTRACTOR,
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

    async def extract(
        self,
        file_path: Path,
        options: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        start_time = time.perf_counter()
        content = ""
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            content = "[Mock extractor: could not decode file]"

        elements = [
            ExtractedElement(
                element_type="text",
                content=content,
                page_number=1,
                confidence=1.0,
                metadata={"length": len(content)},
            )
        ]

        duration = time.perf_counter() - start_time
        return ExtractionResult(
            engine_name=self.metadata.name,
            elements=elements,
            raw_text=content,
            page_count=1,
            metadata={"sample_mode": True},
            execution_time_seconds=round(duration, 4),
        )
