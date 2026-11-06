"""Image adapter converting ImageDocument to UniversalContent with genuine OCR extraction."""

from app.modules.converters.schemas import (
    UniversalContent,
    UniversalSection,
    UniversalTable,
)
from app.modules.image_intelligence.schemas.image_document import ImageDocument, RegionType


class ImageAdapter:
    """Adapts ImageDocument into standard UniversalContent based strictly on genuine OCR and metadata."""

    @classmethod
    def adapt(cls, doc: ImageDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or doc.filename
        paragraphs: list[str] = []
        sections: list[UniversalSection] = []
        tables: list[UniversalTable] = []

        # 1. Genuine OCR text lines
        raw_ocr = doc.analysis.ocr_full_text.strip()
        if raw_ocr:
            for line in raw_ocr.splitlines():
                c_line = line.strip()
                if c_line:
                    paragraphs.append(c_line)

        # 2. Text regions sorted by reading order or vertical position
        text_regions = [r for r in doc.regions if r.region_type == RegionType.TEXT and r.text]
        if text_regions:
            text_regions.sort(key=lambda r: (r.reading_order if r.reading_order is not None else 0, r.bounding_box[0]))
            region_texts = [r.text.strip() for r in text_regions if r.text and r.text.strip()]
            if not paragraphs and region_texts:
                paragraphs = region_texts

            # Add structured OCR region table if requested/useful
            region_rows = [
                [
                    str(r.region_id),
                    str(r.text).strip(),
                    f"[{r.bounding_box[0]:.2f}, {r.bounding_box[1]:.2f}, {r.bounding_box[2]:.2f}, {r.bounding_box[3]:.2f}]",
                    f"{r.confidence:.2f}",
                ]
                for r in text_regions
            ]
            tables.append(
                UniversalTable(
                    title="OCR Bounding Box Regions",
                    headers=["Region ID", "Extracted Text", "Bounding Box [ymin, xmin, ymax, xmax]", "Confidence"],
                    rows=region_rows,
                    row_count=len(region_rows),
                    col_count=4,
                )
            )

        # Section: OCR Text
        if paragraphs:
            sections.append(
                UniversalSection(
                    title="Extracted Text (OCR)",
                    content="\n\n".join(paragraphs),
                )
            )

        # Metadata
        meta = {
            "width": doc.metadata.width,
            "height": doc.metadata.height,
            "format": doc.metadata.format,
            "color_mode": doc.metadata.color_mode,
            "ocr_confidence": doc.analysis.ocr_average_confidence,
            "ocr_word_count": doc.analysis.ocr_word_count,
        }

        all_text = "\n\n".join(paragraphs) if paragraphs else ""
        return UniversalContent(
            source_filename=filename,
            source_format=doc.metadata.format.lower(),
            title=f"Image: {filename}",
            author="",
            page_count=1,
            word_count=len(all_text.split()),
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            metadata=meta,
            warnings=[],
            raw_text=all_text,
        )
