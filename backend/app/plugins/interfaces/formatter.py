"""Output formatter plugin interface."""

from abc import abstractmethod
from typing import Any

from app.plugins.interfaces.base import ProcessingPluginInterface
from app.plugins.interfaces.extractor import ExtractionResult


class OutputFormatterInterface(ProcessingPluginInterface):
    """Interface for formatting extraction results into target file types (MD, JSON, TXT)."""

    @property
    @abstractmethod
    def target_format(self) -> str:
        """Target format identifier (e.g. 'markdown', 'json', 'text', 'csv')."""
        pass

    @abstractmethod
    async def format(
        self,
        result: ExtractionResult,
        options: dict[str, Any] | None = None,
    ) -> bytes:
        """Format extraction result into target representation bytes."""
        pass
