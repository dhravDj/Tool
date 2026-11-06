"""DOCX Document Extraction Adapter using python-docx."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import docx
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.domain.enums import BlockType, ExtractionStatus
from app.domain.schemas.canonical_document import (
    CanonicalBlock,
    CanonicalDocument,
    CanonicalPage,
)
from app.modules.extraction.adapters.base import (
    BaseDocumentExtractor,
    CorruptedDocumentError,
)

logger = logging.getLogger(__name__)


class DocxExtractor(BaseDocumentExtractor):
    """Structured extraction adapter for modern Word DOCX documents."""

    engine_name = "docx_extractor"
    version = "1.2.0"
    supported_formats = ["docx"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract paragraphs, headings, tables, headers, footers, and metadata."""
        return await asyncio.to_thread(
            self._extract_sync,
            file_path,
            original_filename or file_path.name,
            options or {},
        )

    def _extract_sync(
        self,
        file_path: Path,
        original_filename: str,
        options: dict[str, Any],
    ) -> CanonicalDocument:
        doc_id = options.get("document_id") or uuid.uuid4().hex

        try:
            doc = docx.Document(str(file_path))
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to read DOCX document: {exc}") from exc

        # 1. Extract Core Properties / Metadata
        props = doc.core_properties
        metadata: dict[str, Any] = {
            "title": props.title or None,
            "author": props.author or None,
            "subject": props.subject or None,
            "keywords": props.keywords or None,
            "category": props.category or None,
            "comments": props.comments or None,
            "created": props.created.isoformat() if props.created else None,
            "modified": props.modified.isoformat() if props.modified else None,
            "revision": props.revision or None,
            "last_modified_by": props.last_modified_by or None,
        }

        # 2. Extract Hyperlink Relationships map
        hyperlinks_map: dict[str, str] = {}
        try:
            rels = doc.part.rels
            for rel_id, rel in rels.items():
                if rel.reltype == RELATIONSHIP_TYPE.HYPERLINK:
                    hyperlinks_map[rel_id] = rel.target_ref
        except Exception as exc:
            logger.debug(f"Could not read hyperlinks map: {exc}")

        pages: list[CanonicalPage] = []
        all_blocks: list[CanonicalBlock] = []
        warnings: list[str] = []
        errors: list[str] = []

        current_page_number = 1
        current_page_blocks: list[CanonicalBlock] = []
        global_reading_order = 0

        # Helper to seal current page
        def _seal_page() -> None:
            nonlocal current_page_number, current_page_blocks
            pages.append(
                CanonicalPage(
                    page_number=current_page_number,
                    is_scanned=False,
                    ocr_applied=False,
                    blocks=list(current_page_blocks),
                    metadata={"block_count": len(current_page_blocks)},
                )
            )
            current_page_number += 1
            current_page_blocks = []

        # 3. Extract Headers and Footers from Sections
        for s_idx, section in enumerate(doc.sections):
            header = section.header
            if header and not header.is_linked_to_previous:
                for hp in header.paragraphs:
                    htext = hp.text.strip()
                    if htext:
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(
                                current_page_number, len(current_page_blocks)
                            ),
                            block_type=BlockType.HEADER,
                            text=htext,
                            reading_order=global_reading_order,
                            page_number=current_page_number,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native_header",
                            metadata={"section_index": s_idx},
                        )
                        current_page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

        # 4. Extract Document Body in Sequential Order (Paragraphs and Tables)
        # Using doc.element.body to preserve intermixed paragraph and table ordering
        body_elements = doc.element.body
        for child in body_elements:
            # Check for page break in paragraph
            if child.tag.endswith("p"):
                p = Paragraph(child, doc)
                text = p.text.strip()

                # Check if paragraph contains explicit page break
                xml_str = child.xml
                has_page_break = 'w:type="page"' in xml_str or "w:lastRenderedPageBreak" in xml_str

                if text:
                    style_name = p.style.name.lower() if p.style and p.style.name else ""
                    b_type, meta = self._classify_paragraph(p, style_name, hyperlinks_map)

                    block = CanonicalBlock(
                        block_id=self._generate_block_id(
                            current_page_number, len(current_page_blocks)
                        ),
                        block_type=b_type,
                        text=text,
                        reading_order=global_reading_order,
                        page_number=current_page_number,
                        confidence=1.0,
                        extraction_engine=self.engine_name,
                        provenance="native",
                        metadata=meta,
                    )
                    current_page_blocks.append(block)
                    all_blocks.append(block)
                    global_reading_order += 1

                if has_page_break and current_page_blocks:
                    _seal_page()

            elif child.tag.endswith("tbl"):
                tbl = Table(child, doc)
                grid: list[list[str]] = []
                for row in tbl.rows:
                    row_data = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                    grid.append(row_data)

                if grid:
                    table_text = self._format_table_text(grid)
                    block = CanonicalBlock(
                        block_id=self._generate_block_id(
                            current_page_number, len(current_page_blocks)
                        ),
                        block_type=BlockType.TABLE,
                        text=table_text,
                        reading_order=global_reading_order,
                        page_number=current_page_number,
                        confidence=1.0,
                        extraction_engine=self.engine_name,
                        provenance="native_table",
                        metadata={
                            "table_grid": grid,
                            "row_count": len(grid),
                            "col_count": len(grid[0]) if grid else 0,
                        },
                    )
                    current_page_blocks.append(block)
                    all_blocks.append(block)
                    global_reading_order += 1

        # 5. Extract Footers
        for s_idx, section in enumerate(doc.sections):
            footer = section.footer
            if footer and not footer.is_linked_to_previous:
                for fp in footer.paragraphs:
                    ftext = fp.text.strip()
                    if ftext:
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(
                                current_page_number, len(current_page_blocks)
                            ),
                            block_type=BlockType.FOOTER,
                            text=ftext,
                            reading_order=global_reading_order,
                            page_number=current_page_number,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native_footer",
                            metadata={"section_index": s_idx},
                        )
                        current_page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

        # Seal final page if blocks remain or document was empty
        if current_page_blocks or not pages:
            _seal_page()

        self._check_page_limit(len(pages))

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="docx",
            extraction_status=ExtractionStatus.COMPLETED,
            metadata=metadata,
            page_count=len(pages),
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=pages,
            blocks=all_blocks,
            warnings=warnings,
            errors=errors,
        )

    def _classify_paragraph(
        self,
        p: Paragraph,
        style_name: str,
        hyperlinks_map: dict[str, str],
    ) -> tuple[BlockType, dict[str, Any]]:
        meta: dict[str, Any] = {"style": style_name}

        # Check links inside paragraph runs
        urls = []
        for element in p._element.iter():
            if element.tag.endswith("hyperlink"):
                r_id = element.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                )
                if r_id and r_id in hyperlinks_map:
                    urls.append(hyperlinks_map[r_id])
        if urls:
            meta["hyperlinks"] = urls

        if "heading 1" in style_name:
            meta["heading_level"] = 1
            return BlockType.HEADING, meta
        elif "heading 2" in style_name:
            meta["heading_level"] = 2
            return BlockType.HEADING, meta
        elif "heading 3" in style_name:
            meta["heading_level"] = 3
            return BlockType.HEADING, meta
        elif "heading" in style_name:
            meta["heading_level"] = 4
            return BlockType.HEADING, meta
        elif "list" in style_name or "bullet" in style_name:
            meta["list_type"] = "bullet" if "bullet" in style_name else "number"
            return BlockType.LIST_ITEM, meta
        elif "code" in style_name or "preformatted" in style_name:
            return BlockType.CODE, meta
        elif "title" in style_name:
            meta["heading_level"] = 1
            return BlockType.HEADING, meta
        elif "subtitle" in style_name:
            meta["heading_level"] = 2
            return BlockType.HEADING, meta

        return BlockType.PARAGRAPH, meta

    def _format_table_text(self, grid: list[list[str]]) -> str:
        if not grid:
            return ""
        lines: list[str] = []
        for row in grid:
            cells = [c.replace("\n", " ").strip() for c in row]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)
