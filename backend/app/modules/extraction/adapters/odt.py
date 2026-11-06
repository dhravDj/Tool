"""OpenDocument Text (ODT) Document Extraction Adapter."""

import asyncio
import logging
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

# Common OpenDocument XML Namespaces
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
}


class ODTExtractor(BaseDocumentExtractor):
    """Extraction adapter for OpenDocument Text (.odt) files."""

    engine_name = "odt_extractor"
    version = "1.0.0"
    supported_formats = ["odt"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract content, tables, and metadata from an ODT file."""
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

        if not zipfile.is_zipfile(str(file_path)):
            raise CorruptedDocumentError(
                f"File '{original_filename}' is not a valid ZIP-based OpenDocument archive."
            )

        metadata: dict[str, Any] = {}
        warnings: list[str] = []

        try:
            with zipfile.ZipFile(str(file_path), "r") as zf:
                # 1. Parse meta.xml if available
                if "meta.xml" in zf.namelist():
                    try:
                        meta_xml = zf.read("meta.xml")
                        meta_root = ET.fromstring(meta_xml)
                        office_meta = meta_root.find("office:meta", NS)
                        if office_meta is not None:
                            title_el = office_meta.find("dc:title", NS)
                            creator_el = office_meta.find("dc:creator", NS)
                            desc_el = office_meta.find("dc:description", NS)
                            date_el = office_meta.find("dc:date", NS)

                            metadata = {
                                "title": title_el.text if title_el is not None else None,
                                "author": creator_el.text if creator_el is not None else None,
                                "description": desc_el.text if desc_el is not None else None,
                                "created": date_el.text if date_el is not None else None,
                            }
                    except Exception as exc:
                        warnings.append(f"Failed to parse ODT metadata: {exc}")

                # 2. Parse content.xml
                if "content.xml" not in zf.namelist():
                    raise CorruptedDocumentError(
                        f"ODT archive '{original_filename}' is missing 'content.xml'."
                    )

                content_xml = zf.read("content.xml")
                root = ET.fromstring(content_xml)
        except Exception as exc:
            if isinstance(exc, CorruptedDocumentError):
                raise
            raise CorruptedDocumentError(f"Failed to read ODT archive: {exc}") from exc

        # Find the text body: office:body / office:text
        body_text = root.find(".//office:body/office:text", NS)
        if body_text is None:
            body_text = root.find(".//office:text", NS)

        blocks: list[CanonicalBlock] = []
        global_order = 0

        if body_text is not None:
            for el in body_text:
                tag = el.tag

                # Heading: text:h
                if tag == f"{{{NS['text']}}}h":
                    htext = "".join(el.itertext()).strip()
                    if htext:
                        lvl_attr = el.get(f"{{{NS['text']}}}outline-level", "1")
                        try:
                            lvl = int(lvl_attr)
                        except ValueError:
                            lvl = 1

                        block = CanonicalBlock(
                            block_id=self._generate_block_id(1, len(blocks)),
                            block_type=BlockType.HEADING,
                            text=htext,
                            reading_order=global_order,
                            page_number=1,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native",
                            metadata={"heading_level": lvl},
                        )
                        blocks.append(block)
                        global_order += 1

                # Paragraph: text:p
                elif tag == f"{{{NS['text']}}}p":
                    ptext = "".join(el.itertext()).strip()
                    if ptext:
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(1, len(blocks)),
                            block_type=BlockType.PARAGRAPH,
                            text=ptext,
                            reading_order=global_order,
                            page_number=1,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native",
                        )
                        blocks.append(block)
                        global_order += 1

                # List: text:list
                elif tag == f"{{{NS['text']}}}list":
                    for item in el.findall(f".//{{{NS['text']}}}list-item", NS):
                        litext = "".join(item.itertext()).strip()
                        if litext:
                            block = CanonicalBlock(
                                block_id=self._generate_block_id(1, len(blocks)),
                                block_type=BlockType.LIST_ITEM,
                                text=litext,
                                reading_order=global_order,
                                page_number=1,
                                confidence=1.0,
                                extraction_engine=self.engine_name,
                                provenance="native",
                                metadata={"list_type": "bullet"},
                            )
                            blocks.append(block)
                            global_order += 1

                # Table: table:table
                elif tag == f"{{{NS['table']}}}table":
                    grid: list[list[str]] = []
                    for row in el.findall(f".//{{{NS['table']}}}table-row", NS):
                        row_cells: list[str] = []
                        for cell in row.findall(f".//{{{NS['table']}}}table-cell", NS):
                            ctext = "".join(cell.itertext()).strip()
                            row_cells.append(ctext)
                        if row_cells:
                            grid.append(row_cells)

                    if grid:
                        lines = ["| " + " | ".join(r) + " |" for r in grid]
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(1, len(blocks)),
                            block_type=BlockType.TABLE,
                            text="\n".join(lines),
                            reading_order=global_order,
                            page_number=1,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native_table",
                            metadata={"table_grid": grid, "row_count": len(grid)},
                        )
                        blocks.append(block)
                        global_order += 1

        page = CanonicalPage(
            page_number=1,
            is_scanned=False,
            ocr_applied=False,
            blocks=blocks,
            metadata={"block_count": len(blocks)},
        )

        status = (
            ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED
        )

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="odt",
            extraction_status=status,
            metadata=metadata,
            page_count=1,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=[page],
            blocks=blocks,
            warnings=warnings,
            errors=[],
        )
