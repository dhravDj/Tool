"""Document adapter converting CanonicalDocument to UniversalContent."""

from typing import Any

from app.domain.enums import BlockType
from app.domain.schemas.canonical_document import CanonicalDocument
from app.modules.converters.schemas import (
    UniversalCodeBlock,
    UniversalContent,
    UniversalSection,
    UniversalTable,
)


class DocumentAdapter:
    """Adapts CanonicalDocument into standard UniversalContent."""

    @classmethod
    def adapt(cls, doc: CanonicalDocument) -> UniversalContent:
        sections: list[UniversalSection] = []
        paragraphs: list[str] = []
        tables: list[UniversalTable] = []
        code_blocks: list[UniversalCodeBlock] = []

        current_section_title = "Introduction"
        current_section_level = 1
        current_section_content: list[str] = []
        current_page = 1

        for block in doc.blocks:
            text = block.text.strip()
            if not text and block.block_type != BlockType.TABLE:
                continue

            current_page = block.page_number

            if block.block_type == BlockType.HEADING:
                if current_section_content:
                    sections.append(
                        UniversalSection(
                            title=current_section_title,
                            level=current_section_level,
                            content="\n\n".join(current_section_content),
                            page_or_slide_number=current_page,
                        )
                    )
                    current_section_content = []
                current_section_title = text
                current_section_level = int(block.metadata.get("heading_level", 1))

            elif block.block_type == BlockType.PARAGRAPH:
                paragraphs.append(text)
                current_section_content.append(text)

            elif block.block_type in (BlockType.LIST, BlockType.LIST_ITEM):
                paragraphs.append(f"• {text}")
                current_section_content.append(f"• {text}")

            elif block.block_type == BlockType.CODE:
                lang = block.metadata.get("language", "")
                code_blocks.append(
                    UniversalCodeBlock(
                        language=lang,
                        code=text,
                        caption=block.metadata.get("caption", ""),
                        line_count=len(text.splitlines()),
                    )
                )
                current_section_content.append(f"```{lang}\n{text}\n```")

            elif block.block_type == BlockType.TABLE:
                grid: list[list[Any]] | None = block.metadata.get("grid")
                if grid and isinstance(grid, list) and len(grid) > 0:
                    headers = [str(c) for c in grid[0]]
                    rows = grid[1:] if len(grid) > 1 else []
                    tables.append(
                        UniversalTable(
                            title=block.metadata.get("title", f"Table (Page {current_page})"),
                            headers=headers,
                            rows=rows,
                            row_count=len(rows),
                            col_count=len(headers),
                        )
                    )
                else:
                    # Fallback text representation of table
                    paragraphs.append(text)
                    current_section_content.append(text)

        # Flush final section
        if current_section_content or current_section_title != "Introduction":
            sections.append(
                UniversalSection(
                    title=current_section_title,
                    level=current_section_level,
                    content="\n\n".join(current_section_content),
                    page_or_slide_number=current_page,
                )
            )

        # Calculate word count
        all_text = " ".join(paragraphs) + " " + " ".join(s.content for s in sections)
        word_count = len(all_text.split())

        return UniversalContent(
            source_filename=doc.original_filename,
            source_format=doc.detected_format,
            title=str(doc.metadata.get("title") or doc.original_filename or "Document"),
            author=str(doc.metadata.get("author") or ""),
            page_count=max(1, doc.page_count),
            word_count=word_count,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            code_blocks=code_blocks,
            metadata=doc.metadata,
            warnings=doc.warnings,
            raw_text=all_text.strip(),
        )
