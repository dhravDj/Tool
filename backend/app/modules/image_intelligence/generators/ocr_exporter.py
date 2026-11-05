"""Plain OCR text export generator."""

from app.modules.image_intelligence.schemas.image_document import ImageDocument, RegionType


class ImageOCRExporter:
    """Exports OCR-recognized text in normalized reading order."""

    @staticmethod
    def export(doc: ImageDocument) -> str:
        """Extract clean text lines in reading order."""
        if doc.analysis.ocr_full_text:
            return doc.analysis.ocr_full_text

        text_regions = [r for r in doc.regions if r.region_type == RegionType.TEXT and r.text]
        # Sort by reading order
        text_regions.sort(key=lambda r: r.reading_order if r.reading_order is not None else 0)
        return " ".join(r.text.strip() for r in text_regions if r.text)
