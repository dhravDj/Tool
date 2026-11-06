"""Optical Character Recognition (OCR) engine with word & line bounding boxes and reading order."""

import logging
import shutil
from typing import Any

from PIL import Image

from app.core.config import settings
from app.modules.image_intelligence.schemas.image_document import ImageRegion, RegionType

logger = logging.getLogger(__name__)

try:
    import pytesseract

    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class ImageOCREngine:
    """Extracts text, word coordinates, confidence scores, and reading order."""

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        self.tesseract_cmd = tesseract_cmd or shutil.which("tesseract")
        if self.tesseract_cmd and HAS_PYTESSERACT:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    @property
    def is_available(self) -> bool:
        if not (settings.OCR_ENABLED and HAS_PYTESSERACT and self.tesseract_cmd):
            return False
        import os

        return bool(shutil.which(self.tesseract_cmd) or os.path.exists(self.tesseract_cmd))

    def extract_regions(
        self,
        img: Image.Image,
        options: dict[str, Any] | None = None,
    ) -> tuple[list[ImageRegion], str, float, list[str]]:
        """Run OCR on image and return (text_regions, full_text, avg_confidence, warnings)."""
        options = options or {}
        warnings: list[str] = []
        width, height = img.size

        if not self.is_available:
            warnings.append(
                "OCR engine (Tesseract) is unavailable on this host; text extraction was skipped."
            )
            return [], "", 0.0, warnings

        try:
            config = options.get("tesseract_config", "--psm 1 --oem 3")
            data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT, config=config
            )

            n_boxes = len(data.get("text", []))
            raw_words: list[dict[str, Any]] = []

            for i in range(n_boxes):
                text = str(data["text"][i]).strip()
                if not text:
                    continue

                conf_raw = float(data["conf"][i])
                if conf_raw < 0:
                    continue

                conf = round(conf_raw / 100.0, 3)
                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])

                raw_words.append(
                    {
                        "text": text,
                        "conf": conf,
                        "x0": x,
                        "y0": y,
                        "x1": x + w,
                        "y1": y + h,
                        "line_num": data.get("line_num", [0])[i],
                        "block_num": data.get("block_num", [0])[i],
                    }
                )

            # Sort and assemble reading order
            sorted_words = self._sort_reading_order(raw_words)

            regions: list[ImageRegion] = []
            full_text_parts: list[str] = []
            confidences: list[float] = []

            for order_idx, item in enumerate(sorted_words):
                w_conf = item["conf"]
                confidences.append(w_conf)
                full_text_parts.append(item["text"])

                ymin = round(item["y0"] / max(1, height), 4)
                xmin = round(item["x0"] / max(1, width), 4)
                ymax = round(item["y1"] / max(1, height), 4)
                xmax = round(item["x1"] / max(1, width), 4)

                regions.append(
                    ImageRegion(
                        region_id=f"text_word_{order_idx + 1}",
                        region_type=RegionType.TEXT,
                        bounding_box=[ymin, xmin, ymax, xmax],
                        pixel_box=[item["x0"], item["y0"], item["x1"], item["y1"]],
                        label="text_word",
                        text=item["text"],
                        confidence=w_conf,
                        provenance="ocr",
                        reading_order=order_idx,
                        attributes={
                            "low_confidence": w_conf < 0.60,
                            "line_num": item["line_num"],
                            "block_num": item["block_num"],
                        },
                    )
                )

            full_text = " ".join(full_text_parts)
            avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

            return regions, full_text, avg_conf, warnings

        except Exception as exc:
            logger.error(f"OCR execution failure: {exc}")
            warnings.append(f"OCR processing failed: {exc}")
            return [], "", 0.0, warnings

    def _sort_reading_order(self, words: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group words into horizontal text lines and sort left-to-right, top-to-bottom."""
        if not words:
            return []

        # Sort primarily by y0, secondary by x0
        sorted_by_y = sorted(words, key=lambda w: (w["y0"], w["x0"]))

        lines: list[list[dict[str, Any]]] = []
        current_line: list[dict[str, Any]] = [sorted_by_y[0]]

        for word in sorted_by_y[1:]:
            last_word = current_line[-1]
            h = max(last_word["y1"] - last_word["y0"], 12)
            # If vertical overlap is significant, words belong to the same line
            if abs(word["y0"] - last_word["y0"]) <= (h * 0.5):
                current_line.append(word)
            else:
                current_line.sort(key=lambda w: w["x0"])
                lines.append(current_line)
                current_line = [word]

        if current_line:
            current_line.sort(key=lambda w: w["x0"])
            lines.append(current_line)

        # Flatten lines in reading order
        ordered: list[dict[str, Any]] = []
        for line in lines:
            ordered.extend(line)

        return ordered
