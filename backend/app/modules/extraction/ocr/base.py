"""Base interface for OCR adapters."""

from abc import ABC, abstractmethod
from typing import Any


class OCRAdapterInterface(ABC):
    """Abstract contract for OCR processing engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the OCR engine."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether the OCR engine and its underlying system binaries are available."""
        pass

    @abstractmethod
    async def extract_text_from_image(
        self,
        image_bytes: bytes,
        options: dict[str, Any] | None = None,
    ) -> tuple[str, float]:
        """Extract text from rasterized page image bytes.

        Returns:
            tuple[str, float]: (extracted_text, confidence_score_0_to_1)
        """
        pass
