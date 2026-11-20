"""Adapter converting Universal-Converter Document/PaperModel/WorkbookModel into DocuMind UniversalContent."""

from pathlib import Path
from typing import Any

from app.modules.converters.schemas import (
    UniversalCodeBlock,
    UniversalContent,
    UniversalSection,
    UniversalTable,
)


class ConverterEngineAdapter:
    """Adapts objects from converter_engine into standard DocuMind UniversalContent."""

    @classmethod
    def adapt(cls, doc_obj: Any, original_filename: str, source_format: str) -> UniversalContent:
        # If object has to_document(), convert it first (e.g. PaperModel, WorkbookModel)
        if hasattr(doc_obj, "to_document") and callable(doc_obj.to_document):
            doc = doc_obj.to_document()
        else:
            doc = doc_obj

        sections: list[UniversalSection] = []
        paragraphs: list[str] = []
        tables: list[UniversalTable] = []
        code_blocks: list[UniversalCodeBlock] = []

        title = getattr(doc, "title", "") or ""
        if not title:
            title = Path(original_filename).stem.replace("_", " ").title()

        meta_obj = getattr(doc, "metadata", None)
        author = ""
        meta_dict: dict[str, Any] = {}
        if meta_obj is not None:
            if hasattr(meta_obj, "to_dict") and callable(meta_obj.to_dict):
                meta_dict = meta_obj.to_dict()
            elif isinstance(meta_obj, dict):
                meta_dict = dict(meta_obj)
            author = str(getattr(meta_obj, "author", "") or meta_dict.get("author", "") or "")

        # Extract blocks if available
        blocks = getattr(doc, "blocks", []) or []
        current_section_title = "Introduction"
        current_section_level = 1
        current_section_content: list[str] = []

        for block in blocks:
            b_type = getattr(block, "type", "paragraph")
            if b_type == "heading":
                text = getattr(block, "text", "").strip()
                if current_section_content or (current_section_title and current_section_title != "Introduction"):
                    sections.append(
                        UniversalSection(
                            title=current_section_title,
                            level=current_section_level,
                            content="\n\n".join(current_section_content),
                        )
                    )
                    current_section_content = []
                current_section_title = text
                current_section_level = int(getattr(block, "level", 1))

            elif b_type == "paragraph":
                text = getattr(block, "text", "").strip()
                if text:
                    paragraphs.append(text)
                    current_section_content.append(text)

            elif b_type in ("list", "list_item"):
                items = getattr(block, "items", [])
                for itm in items:
                    itm_str = str(itm.get("text", "") if isinstance(itm, dict) else itm).strip()
                    if itm_str:
                        paragraphs.append(f"• {itm_str}")
                        current_section_content.append(f"• {itm_str}")

            elif b_type == "table":
                headers = [str(h) for h in getattr(block, "headers", [])]
                rows = getattr(block, "rows", [])
                clean_rows = [[str(c) for c in r] for r in rows] if rows else []
                tables.append(
                    UniversalTable(
                        title=getattr(block, "caption", "") or f"Table {len(tables) + 1}",
                        headers=headers,
                        rows=clean_rows,
                        row_count=len(clean_rows),
                        col_count=len(headers) if headers else (len(clean_rows[0]) if clean_rows else 0),
                    )
                )

            elif b_type == "code":
                code_text = getattr(block, "code", "")
                lang = getattr(block, "language", "") or ""
                code_blocks.append(
                    UniversalCodeBlock(
                        language=lang,
                        code=code_text,
                        caption=getattr(block, "caption", ""),
                        line_count=len(code_text.splitlines()),
                    )
                )
                current_section_content.append(f"```{lang}\n{code_text}\n```")

        # Flush final section
        if current_section_content or current_section_title != "Introduction":
            sections.append(
                UniversalSection(
                    title=current_section_title,
                    level=current_section_level,
                    content="\n\n".join(current_section_content),
                )
            )

        raw_text = getattr(doc, "text", "") or "\n\n".join(paragraphs)
        word_count = len(raw_text.split())

        warnings = [str(w) for w in getattr(doc, "warnings", [])]

        return UniversalContent(
            source_filename=original_filename,
            source_format=source_format,
            title=title,
            author=author,
            page_count=getattr(doc, "page_count", 1) or (len(getattr(doc, "pages", [])) if hasattr(doc, "pages") else 1) or 1,
            word_count=word_count,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            code_blocks=code_blocks,
            metadata=meta_dict,
            warnings=warnings,
            raw_text=raw_text,
        )
