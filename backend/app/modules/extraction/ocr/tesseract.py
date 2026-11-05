"""Tesseract OCR adapter using pytesseract."""

import asyncio
import io
import shutil
from typing import Any

from PIL import Image

from app.core.logging import logger
from app.modules.extraction.ocr.base import OCRAdapterInterface

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class TesseractOCRAdapter(OCRAdapterInterface):
    """Production Tesseract OCR engine adapter with asynchronous thread execution."""

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        self._tesseract_cmd = tesseract_cmd or shutil.which("tesseract")
        if self._tesseract_cmd and HAS_PYTESSERACT:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

    @property
    def name(self) -> str:
        return "tesseract"

    @property
    def is_available(self) -> bool:
        return bool(HAS_PYTESSERACT and self._tesseract_cmd)

    async def extract_text_from_image(
        self,
        image_bytes: bytes,
        options: dict[str, Any] | None = None,
    ) -> tuple[str, float]:
        """Extract text and confidence score from image bytes without blocking the event loop."""
        if not self.is_available:
            logger.warning("Tesseract OCR is not available on this host.")
            return "", 0.0

        return await asyncio.to_thread(self._sync_extract, image_bytes, options or {})

    def _sync_extract(self, image_bytes: bytes, options: dict[str, Any]) -> tuple[str, float]:
        try:
            raw_img = Image.open(io.BytesIO(image_bytes))
            img: Image.Image = raw_img.convert("RGB") if raw_img.mode not in ("RGB", "L") else raw_img

            # Extract detailed OCR data including word-level confidence
            data = pytesseract.image_to_data(
                img,
                output_type=pytesseract.Output.DICT,
                config=options.get("tesseract_config", "--psm 1 --oem 3"),
            )

            words: list[str] = []
            confidences: list[float] = []

            for i, text in enumerate(data.get("text", [])):
                word = text.strip()
                if word:
                    words.append(word)
                    try:
                        conf = float(data["conf"][i])
                        if conf >= 0:
                            confidences.append(conf)
                    except (ValueError, KeyError, IndexError):
                        pass

            extracted_text = " ".join(words)
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            return extracted_text, round(avg_conf, 3)

        except Exception as e:
            logger.error(f"Error during Tesseract OCR extraction: {e}")
            return "", 0.0
