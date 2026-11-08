"""Intelligent OCR routing for scanned and mixed document pages."""

from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.domain.enums import BlockType
from app.domain.schemas.canonical_document import CanonicalBlock
from app.modules.extraction.ocr.base import OCRAdapterInterface
from app.modules.extraction.ocr.tesseract import TesseractOCRAdapter


class OCRRouter:
    """Evaluates page text density and routes scanned pages to OCR engines without duplicating text."""

    def __init__(self, adapter: OCRAdapterInterface | None = None) -> None:
        self.adapter = adapter or TesseractOCRAdapter()

    def is_ocr_available(self) -> bool:
        return settings.OCR_ENABLED and self.adapter.is_available

    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic status of OCR routing and underlying adapter."""
        adapter_diag = {}
        if hasattr(self.adapter, "get_diagnostics"):
            adapter_diag = self.adapter.get_diagnostics()

        return {
            "ocr_enabled_in_settings": settings.OCR_ENABLED,
            "density_threshold_chars": settings.OCR_DENSITY_THRESHOLD_CHARS,
            "is_ready": self.is_ocr_available(),
            "adapter": adapter_diag,
        }

    def should_route_to_ocr(
        self,
        char_count: int,
        has_images: bool,
        is_force_ocr: bool = False,
    ) -> bool:
        """Determine if a page requires OCR processing."""
        if not settings.OCR_ENABLED:
            return False
        if is_force_ocr:
            return True
        # If the page has almost no digital text but has images, it is likely a scanned document page
        return char_count < settings.OCR_DENSITY_THRESHOLD_CHARS and has_images

    def process_scanned_page_sync(
        self,
        page_number: int,
        image_bytes: bytes,
        start_reading_order: int,
        options: dict[str, Any] | None = None,
    ) -> tuple[list[CanonicalBlock], list[str]]:
        """Synchronously execute OCR on a scanned page image and return generated canonical blocks."""
        blocks: list[CanonicalBlock] = []
        warnings: list[str] = []

        if not self.is_ocr_available():
            warnings.append(
                f"Page {page_number} has low digital text density but OCR engine is unavailable or disabled."
            )
            return blocks, warnings

        try:
            if hasattr(self.adapter, "extract_text_sync"):
                text, conf = self.adapter.extract_text_sync(image_bytes, options)
            elif hasattr(self.adapter, "_sync_extract"):
                text, conf = self.adapter._sync_extract(image_bytes, options or {})
            else:
                import asyncio
                text, conf = asyncio.run(self.adapter.extract_text_from_image(image_bytes, options))

            text = text.replace("\x00", "").strip()
            if text:
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
                for idx, para in enumerate(paragraphs):
                    block = CanonicalBlock(
                        block_id=f"p{page_number}_ocr_{idx + 1}",
                        block_type=BlockType.PARAGRAPH,
                        text=para,
                        reading_order=start_reading_order + idx,
                        page_number=page_number,
                        confidence=conf,
                        extraction_engine=f"ocr_{self.adapter.name}",
                        provenance="ocr",
                    )
                    blocks.append(block)
            else:
                warnings.append(f"Page {page_number} routed to OCR but no text was recognized.")
        except Exception as e:
            logger.error(f"Failed to process OCR for page {page_number}: {e}")
            warnings.append(f"OCR failure on page {page_number}: {e}")

        return blocks, warnings

    async def process_scanned_page(
        self,
        page_number: int,
        image_bytes: bytes,
        start_reading_order: int,
        options: dict[str, Any] | None = None,
    ) -> tuple[list[CanonicalBlock], list[str]]:
        """Execute OCR on a scanned page image and return generated canonical blocks."""
        blocks: list[CanonicalBlock] = []
        warnings: list[str] = []

        if not self.is_ocr_available():
            warnings.append(
                f"Page {page_number} has low digital text density but OCR engine is unavailable or disabled."
            )
            return blocks, warnings

        try:
            text, conf = await self.adapter.extract_text_from_image(image_bytes, options)
            text = text.strip()
            if text:
                # Divide OCR text by paragraph if double newlines exist
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
                for idx, para in enumerate(paragraphs):
                    block = CanonicalBlock(
                        block_id=f"p{page_number}_ocr_{idx + 1}",
                        block_type=BlockType.PARAGRAPH,
                        text=para,
                        reading_order=start_reading_order + idx,
                        page_number=page_number,
                        confidence=conf,
                        extraction_engine=f"ocr_{self.adapter.name}",
                        provenance="ocr",
                    )
                    blocks.append(block)
            else:
                warnings.append(f"Page {page_number} routed to OCR but no text was recognized.")

        except Exception as e:
            logger.error(f"Failed to process OCR for page {page_number}: {e}")
            warnings.append(f"OCR failure on page {page_number}: {e}")

        return blocks, warnings


# Singleton OCR router instance
ocr_router = OCRRouter()
