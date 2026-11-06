"""Base interface for structured data engines (JSON, XML, YAML, TOML, Parquet)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)


class BaseStructuredEngine(ABC):
    """Abstract base class for structured data parsers and profilers."""

    @property
    @abstractmethod
    def format(self) -> str:
        """Format identifier (e.g. 'json', 'xml', 'yaml', 'toml', 'parquet')."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of handled file extensions."""
        pass

    @abstractmethod
    def analyze(
        self,
        file_path_or_bytes: Path | str | bytes,
        file_id: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> StructuredDataDocument:
        """Analyze structured data payload, extract hierarchy, profile columns, and validate semantics."""
        pass
