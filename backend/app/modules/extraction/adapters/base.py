"""Base document extractor providing a uniform interface and shared utilities."""

import time
import uuid
from abc import abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.domain.enums import ExtractionStatus
from app.domain.schemas.canonical_document import (
    CanonicalDocument,
)
from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.extractor import ExtractionEngineInterface, ExtractionResult


class ExtractionError(Exception):
    """Base exception for document extraction failures."""
    pass


class PasswordRequiredError(ExtractionError):
    """Raised when a document is encrypted or requires a password."""
    pass


class CorruptedDocumentError(ExtractionError):
    """Raised when a document file structure is corrupted or unreadable."""
    pass


class UnsupportedFormatError(ExtractionError):
    """Raised when an extractor cannot handle the provided file format."""
    pass


class PageLimitExceededError(ExtractionError):
    """Raised when a document exceeds the configured maximum page limit."""
    pass


class BaseDocumentExtractor(ExtractionEngineInterface):
    """Abstract base class for all file format extraction adapters."""

    engine_name: str = "base_extractor"
    version: str = "1.0.0"
    supported_formats: list[str] = []

    def __init__(self) -> None:
        self._is_initialized = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.engine_name,
            version=self.version,
            description=f"DocuMind content extractor for {', '.join(self.supported_formats)}",
            plugin_type=PluginType.EXTRACTOR,
            supported_formats=self.supported_formats,
            is_available=True,
        )

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        self._is_initialized = True

    async def shutdown(self) -> None:
        self._is_initialized = False

    async def check_health(self) -> bool:
        return True

    @abstractmethod
    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract content into a structured CanonicalDocument."""
        pass

    async def extract(
        self,
        file_path: Path,
        options: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        """Fulfill the generic ProcessingPluginInterface contract."""
        start_time = time.monotonic()
        doc = await self.extract_document(
            file_path=file_path,
            original_filename=file_path.name,
            options=options,
        )
        elapsed = time.monotonic() - start_time
        return doc.to_extraction_result(execution_time_seconds=elapsed)

    def _generate_block_id(self, page_number: int, index: int) -> str:
        """Create a deterministic or traceable block ID."""
        return f"p{page_number}_b{index}_{uuid.uuid4().hex[:8]}"

    def _check_page_limit(self, page_count: int, max_limit: int | None = None) -> None:
        """Enforce maximum page count safety limit to prevent resource exhaustion."""
        limit = max_limit if max_limit is not None else int(getattr(settings, "MAX_EXTRACTION_PAGE_LIMIT", 1000))
        if page_count > limit:
            raise PageLimitExceededError(
                f"Document page count ({page_count}) exceeds maximum allowed limit ({limit})"
            )

    def _create_empty_document(
        self,
        document_id: str,
        original_filename: str,
        detected_format: str,
        status: ExtractionStatus = ExtractionStatus.FAILED,
        error: str | None = None,
        warnings: list[str] | None = None,
    ) -> CanonicalDocument:
        """Factory for empty/error state documents."""
        errors = [error] if error else []
        return CanonicalDocument(
            document_id=document_id,
            original_filename=original_filename,
            detected_format=detected_format,
            extraction_status=status,
            page_count=0,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=[],
            blocks=[],
            warnings=warnings or [],
            errors=errors,
        )
