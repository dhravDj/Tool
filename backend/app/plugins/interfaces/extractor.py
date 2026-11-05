"""Document extraction engine plugin interface."""

from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.plugins.interfaces.base import ProcessingPluginInterface


@dataclass
class ExtractedElement:
    """Represents a discrete element (heading, paragraph, table, formula, image)."""

    element_type: str  # text | table | image | equation | key_value
    content: Any
    page_number: int | None = None
    bounding_box: list[float] | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Unified output from an extraction engine."""

    engine_name: str
    elements: list[ExtractedElement]
    raw_text: str
    page_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0


class ExtractionEngineInterface(ProcessingPluginInterface):
    """Interface for engines that parse file structures and extract text/tables/images."""

    @abstractmethod
    async def extract(
        self,
        file_path: Path,
        options: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        """Extract structured content from the given file."""
        pass
