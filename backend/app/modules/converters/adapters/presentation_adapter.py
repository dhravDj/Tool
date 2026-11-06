"""Presentation adapter converting PresentationDocument to UniversalContent."""

from app.modules.converters.schemas import (
    UniversalContent,
    UniversalSection,
    UniversalTable,
)
from app.modules.presentation_intelligence.schemas.presentation_document import (
    ElementType,
    PresentationDocument,
)


class PresentationAdapter:
    """Adapts PresentationDocument into standard UniversalContent."""

    @classmethod
    def adapt(cls, doc: PresentationDocument, original_filename: str = "") -> UniversalContent:
        sections: list[UniversalSection] = []
        paragraphs: list[str] = []
        tables: list[UniversalTable] = []

        filename = original_filename or doc.metadata.title or f"presentation.{doc.format}"

        # 1. Slides into Sections
        for slide in doc.slides:
            slide_title = slide.title or f"Slide {slide.slide_number}"
            slide_texts: list[str] = []

            for elem in slide.elements:
                if elem.element_type in (ElementType.TITLE, ElementType.TEXT) and elem.text_frame:
                    for para in elem.text_frame.paragraphs:
                        txt = para.text.strip()
                        if txt:
                            indent = "  " * para.level
                            prefix = "• " if para.is_bullet else ""
                            line = f"{indent}{prefix}{txt}"
                            slide_texts.append(line)
                            paragraphs.append(txt)

            if slide.speaker_notes:
                notes_clean = slide.speaker_notes.strip()
                if notes_clean:
                    slide_texts.append(f"\n[Speaker Notes: {notes_clean}]")

            slide_body = "\n".join(slide_texts).strip()

            sections.append(
                UniversalSection(
                    title=slide_title,
                    level=2,
                    content=slide_body,
                    page_or_slide_number=slide.slide_number,
                )
            )

        # 2. Slide tables
        for stbl in doc.tables:
            tbl_rows: list[list[str]] = []
            for r in stbl.rows:
                tbl_rows.append([c.text.strip() for c in r])

            tables.append(
                UniversalTable(
                    title=f"Slide {stbl.slide_number} Table",
                    headers=stbl.headers or (tbl_rows[0] if tbl_rows else []),
                    rows=tbl_rows[1:] if (stbl.headers and tbl_rows) else tbl_rows,
                    row_count=stbl.rows_count,
                    col_count=stbl.columns_count,
                )
            )

        all_text = "\n\n".join(
            f"Slide {s.page_or_slide_number}: {s.title}\n{s.content}" for s in sections
        )
        word_count = len(all_text.split())

        meta = {
            "author": doc.metadata.author,
            "created_at": doc.metadata.created_at,
            "slide_count": doc.slide_count,
            "table_count": len(doc.tables),
            "chart_count": len(doc.charts),
            "asset_count": len(doc.assets),
        }

        return UniversalContent(
            source_filename=filename,
            source_format=doc.format,
            title=doc.metadata.title or filename,
            author=doc.metadata.author or "",
            page_count=max(1, doc.slide_count),
            word_count=word_count,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            metadata=meta,
            warnings=doc.warnings,
            raw_text=all_text,
        )
