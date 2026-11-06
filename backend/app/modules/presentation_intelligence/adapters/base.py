"""Abstract base adapter for presentation intelligence extraction engines."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.modules.presentation_intelligence.schemas.presentation_document import (
    PresentationDocument,
)


class BasePresentationAdapter(ABC):
    """Abstract base class that all format-specific presentation adapters implement."""

    def __init__(self, format_id: str) -> None:
        self.format_id = format_id

    @abstractmethod
    def can_handle(self, format_id: str) -> bool:
        """Check if this adapter can process the specified format identifier."""
        raise NotImplementedError

    @abstractmethod
    async def extract_presentation(
        self,
        file_path: Path,
        document_id: str,
        file_id: str,
        original_filename: str | None = None,
        max_slides: int = 500,
        options: dict[str, Any] | None = None,
    ) -> tuple[PresentationDocument, list[dict[str, Any]]]:
        """Extract canonical presentation document and embedded raw assets.

        Returns:
            Tuple of (PresentationDocument, list of extracted raw assets metadata/buffers).
        """
        raise NotImplementedError
