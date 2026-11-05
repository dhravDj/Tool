"""EPUB Document Extraction Adapter using ebooklib and BeautifulSoup4."""

import asyncio
import logging
import uuid
import warnings as py_warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ebooklib
from bs4 import BeautifulSoup
from bs4.element import Tag
from ebooklib import epub

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


class EPUBExtractor(BaseDocumentExtractor):
    """Structured extraction adapter for EPUB publications preserving spine reading order."""

    engine_name = "epub_extractor"
    version = "1.0.0"
    supported_formats = ["epub"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract chapters, spine items, metadata, and tables from EPUB."""
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
        extract_images = options.get("extract_images", False)
        assets_dir = options.get("assets_dir")

        try:
            # Suppress noisy ebooklib parser warnings
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("ignore")
                book = epub.read_epub(str(file_path))
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to read EPUB book: {exc}") from exc

        # 1. Extract Dublin Core Metadata
        def _get_dc(field: str) -> str | None:
            vals = book.get_metadata("DC", field)
            return vals[0][0] if vals and vals[0] else None

        metadata: dict[str, Any] = {
            "title": _get_dc("title"),
            "author": _get_dc("creator"),
            "language": _get_dc("language"),
            "identifier": _get_dc("identifier"),
            "publisher": _get_dc("publisher"),
            "date": _get_dc("date"),
        }

        pages: list[CanonicalPage] = []
        all_blocks: list[CanonicalBlock] = []
        warnings: list[str] = []
        errors: list[str] = []
        global_reading_order = 0

        # 2. Extract embedded images if requested
        if extract_images and assets_dir:
            assets_path = Path(assets_dir)
            assets_path.mkdir(parents=True, exist_ok=True)
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                try:
                    img_name = Path(item.get_name()).name
                    out_path = assets_path / img_name
                    content = item.get_content()
                    out_path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
                except Exception as exc:
                    warnings.append(f"Failed to extract EPUB image {item.get_name()}: {exc}")

        # 3. Process documents in Spine Reading Order
        spine_item_ids = [item_id for item_id, _ in book.spine]
        chapter_idx = 0

        for item_id in spine_item_ids:
            doc_item = book.get_item_with_id(item_id)
            if doc_item is None or doc_item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue

            chapter_idx += 1
            page_num = chapter_idx
            html_content = doc_item.get_content()

            try:
                soup = BeautifulSoup(html_content, "html.parser")
            except Exception as exc:
                warnings.append(f"Chapter {page_num}: Failed to parse HTML: {exc}")
                continue

            page_blocks: list[CanonicalBlock] = []

            # Traverse HTML body elements
            body = soup.body or soup
            for el in body.descendants:
                # Process only top-level semantic tags to prevent duplicate nested text
                if not isinstance(el, Tag) or el.name is None:
                    continue

                # Headings h1..h6
                if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    htext = el.get_text().strip()
                    if htext:
                        lvl = int(el.name[1])
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(page_num, len(page_blocks)),
                            block_type=BlockType.HEADING,
                            text=htext,
                            reading_order=global_reading_order,
                            page_number=page_num,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native",
                            metadata={"heading_level": lvl, "spine_id": item_id},
                        )
                        page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

                # Paragraphs
                elif el.name == "p":
                    ptext = el.get_text().strip()
                    if ptext:
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(page_num, len(page_blocks)),
                            block_type=BlockType.PARAGRAPH,
                            text=ptext,
                            reading_order=global_reading_order,
                            page_number=page_num,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native",
                            metadata={"spine_id": item_id},
                        )
                        page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

                # List items (only direct li to avoid duplicate listing)
                elif el.name == "li":
                    litext = el.get_text().strip()
                    if litext:
                        parent_name = el.parent.name if el.parent else "ul"
                        is_num = parent_name == "ol"
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(page_num, len(page_blocks)),
                            block_type=BlockType.LIST_ITEM,
                            text=litext,
                            reading_order=global_reading_order,
                            page_number=page_num,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native",
                            metadata={"list_type": "number" if is_num else "bullet", "spine_id": item_id},
                        )
                        page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

                # Tables
                elif el.name == "table":
                    grid: list[list[str]] = []
                    for row in el.find_all("tr"):
                        cells = [c.get_text().strip() for c in row.find_all(["td", "th"])]
                        if cells:
                            grid.append(cells)
                    if grid:
                        lines = ["| " + " | ".join(r) + " |" for r in grid]
                        block = CanonicalBlock(
                            block_id=self._generate_block_id(page_num, len(page_blocks)),
                            block_type=BlockType.TABLE,
                            text="\n".join(lines),
                            reading_order=global_reading_order,
                            page_number=page_num,
                            confidence=1.0,
                            extraction_engine=self.engine_name,
                            provenance="native_table",
                            metadata={"table_grid": grid, "row_count": len(grid), "spine_id": item_id},
                        )
                        page_blocks.append(block)
                        all_blocks.append(block)
                        global_reading_order += 1

                # Images
                elif el.name == "img":
                    src = el.get("src", "")
                    alt = el.get("alt", "")
                    block = CanonicalBlock(
                        block_id=self._generate_block_id(page_num, len(page_blocks)),
                        block_type=BlockType.IMAGE_REFERENCE,
                        text=f"[Image: {alt or src}]",
                        reading_order=global_reading_order,
                        page_number=page_num,
                        confidence=1.0,
                        extraction_engine=self.engine_name,
                        provenance="native_image",
                        metadata={"src": src, "alt": alt, "spine_id": item_id},
                    )
                    page_blocks.append(block)
                    all_blocks.append(block)
                    global_reading_order += 1

            pages.append(
                CanonicalPage(
                    page_number=page_num,
                    is_scanned=False,
                    ocr_applied=False,
                    blocks=page_blocks,
                    metadata={"spine_id": item_id, "block_count": len(page_blocks)},
                )
            )

        page_count = max(len(pages), 1)
        self._check_page_limit(page_count)

        status = ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="epub",
            extraction_status=status,
            metadata=metadata,
            page_count=page_count,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=pages,
            blocks=all_blocks,
            warnings=warnings,
            errors=errors,
        )
