"""PDF Document Extraction Adapter using PyMuPDF (fitz) with OCR fallback."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pymupdf

from app.core.config import settings
from app.domain.enums import BlockType, ExtractionStatus
from app.domain.schemas.canonical_document import (
    CanonicalBlock,
    CanonicalDocument,
    CanonicalPage,
)
from app.modules.extraction.adapters.base import (
    BaseDocumentExtractor,
    CorruptedDocumentError,
    PasswordRequiredError,
)
from app.modules.extraction.ocr.router import OCRRouter

logger = logging.getLogger(__name__)


class PDFExtractor(BaseDocumentExtractor):
    """High-performance native PDF extractor with table extraction and OCR routing."""

    engine_name = "pymupdf_extractor"
    version = "2.1.0"
    supported_formats = ["pdf"]

    def __init__(self, ocr_router: OCRRouter | None = None) -> None:
        super().__init__()
        self.ocr_router = ocr_router or OCRRouter()

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract pages, blocks, tables, and metadata from a PDF file."""
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
        password = options.get("password")
        extract_images = options.get("extract_images", False)
        extract_tables = options.get("extract_tables", True)
        assets_dir = options.get("assets_dir")

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to open PDF document: {exc}") from exc

        try:
            # Check encryption and password protection
            if doc.is_encrypted:
                if not password or not doc.authenticate(password):
                    raise PasswordRequiredError(
                        f"PDF '{original_filename}' is password-protected or supplied password was invalid."
                    )

            page_count = len(doc)
            self._check_page_limit(page_count, max_limit=options.get("max_page_limit"))

            # Metadata extraction
            raw_meta = doc.metadata or {}
            cleaned_metadata: dict[str, Any] = {
                "title": raw_meta.get("title") or None,
                "author": raw_meta.get("author") or None,
                "subject": raw_meta.get("subject") or None,
                "keywords": raw_meta.get("keywords") or None,
                "creator": raw_meta.get("creator") or None,
                "producer": raw_meta.get("producer") or None,
                "creation_date": raw_meta.get("creationDate") or None,
                "modification_date": raw_meta.get("modDate") or None,
                "format": raw_meta.get("format") or "PDF",
                "page_count": page_count,
            }

            pages: list[CanonicalPage] = []
            all_blocks: list[CanonicalBlock] = []
            warnings: list[str] = []
            errors: list[str] = []
            global_reading_order = 0
            seen_image_ocr: dict[int, str] = {}

            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]
                page_rect = page.rect
                width = float(page_rect.width)
                height = float(page_rect.height)
                rotation = int(page.rotation)

                page_blocks: list[CanonicalBlock] = []
                extracted_table_rects: list[pymupdf.Rect] = []

                # 1. Table Detection via PyMuPDF find_tables() (Configurable)
                if extract_tables:
                    try:
                        tabs = page.find_tables()
                        for tab_idx, tab in enumerate(tabs):
                            tab_rect = pymupdf.Rect(tab.bbox)
                            extracted_table_rects.append(tab_rect)
                            table_data = tab.extract()

                            # Format markdown-like representation of table
                            table_text = self._format_table_text(table_data)

                            block = CanonicalBlock(
                                block_id=self._generate_block_id(page_num, len(page_blocks)),
                                block_type=BlockType.TABLE,
                                text=table_text,
                                reading_order=global_reading_order,
                                page_number=page_num,
                                bounding_box=[tab_rect.x0, tab_rect.y0, tab_rect.x1, tab_rect.y1],
                                confidence=0.95,
                                extraction_engine=self.engine_name,
                                provenance="native_table",
                                metadata={
                                    "table_grid": table_data,
                                    "row_count": len(table_data),
                                    "col_count": len(table_data[0]) if table_data else 0,
                                    "table_index": tab_idx,
                                },
                            )
                            page_blocks.append(block)
                            all_blocks.append(block)
                            global_reading_order += 1
                    except Exception as exc:
                        warnings.append(f"Page {page_num}: Table extraction failed: {exc}")

                # 2. Extract Native Text Blocks with Reading Order Optimization
                text_blocks = page.get_text("blocks")
                sorted_blocks = self._sort_blocks_reading_order(text_blocks, width)

                total_page_digital_chars = 0
                for b_idx, block_tuple in enumerate(sorted_blocks):
                    # block_tuple: (x0, y0, x1, y1, text, block_no, block_type)
                    x0, y0, x1, y1, text, _block_no, b_type = block_tuple[:7]
                    block_rect = pymupdf.Rect(x0, y0, x1, y1)

                    # If block is inside an extracted table, skip duplicate text
                    if any(
                        block_rect in t_rect or t_rect.contains(block_rect)
                        for t_rect in extracted_table_rects
                    ):
                        continue

                    cleaned_text = text.replace("\x00", "").strip()
                    if not cleaned_text:
                        continue

                    total_page_digital_chars += len(cleaned_text)

                    # Classify block type (heading vs paragraph)
                    semantic_type = self._classify_text_block(cleaned_text, y1 - y0)

                    block = CanonicalBlock(
                        block_id=self._generate_block_id(page_num, len(page_blocks)),
                        block_type=semantic_type,
                        text=cleaned_text,
                        reading_order=global_reading_order,
                        page_number=page_num,
                        bounding_box=[float(x0), float(y0), float(x1), float(y1)],
                        confidence=1.0,
                        extraction_engine=self.engine_name,
                        provenance="native",
                        metadata={
                            "block_number": b_idx,
                            "type_code": b_type,
                        },
                    )
                    page_blocks.append(block)
                    all_blocks.append(block)
                    global_reading_order += 1

                # 3. Scanned / Low Digital Text Detection & OCR Routing
                image_list = page.get_images()
                is_scanned = self.ocr_router.should_route_to_ocr(
                    char_count=total_page_digital_chars,
                    has_images=len(image_list) > 0,
                )
                ocr_applied = False

                if is_scanned:
                    if settings.OCR_ENABLED and self.ocr_router.is_ocr_available():
                        try:
                            # Render page to image bytes (150 DPI is fast & accurate)
                            pixmap = page.get_pixmap(dpi=150)
                            img_bytes = pixmap.tobytes("png")

                            # Execute OCR safely without async/await
                            ocr_blocks, ocr_warnings = self.ocr_router.process_scanned_page_sync(
                                page_number=page_num,
                                image_bytes=img_bytes,
                                start_reading_order=global_reading_order,
                                options=options,
                            )

                            warnings.extend(ocr_warnings)
                            if ocr_blocks:
                                ocr_applied = True
                                for ob in ocr_blocks:
                                    page_blocks.append(ob)
                                    all_blocks.append(ob)
                                    global_reading_order += 1
                        except Exception as exc:
                            warnings.append(f"Page {page_num}: OCR processing failed: {exc}")
                    else:
                        warnings.append(
                            f"Page {page_num}: Low digital text detected ({total_page_digital_chars} chars), "
                            "page appears scanned or image-based, but OCR is disabled or unavailable."
                        )
                elif options.get("ocr_enabled", True) and self.ocr_router.is_ocr_available():
                    # Scan embedded images in the middle of a PDF page
                    for img_info in image_list:
                        xref = img_info[0]
                        if xref in seen_image_ocr:
                            cached_text = seen_image_ocr[xref]
                            if cached_text:
                                img_block = CanonicalBlock(
                                    block_id=self._generate_block_id(page_num, len(page_blocks)),
                                    block_type=BlockType.PARAGRAPH,
                                    text=cached_text,
                                    reading_order=global_reading_order,
                                    page_number=page_num,
                                    confidence=0.90,
                                    extraction_engine=f"ocr_embedded_{self.ocr_router.adapter.name}",
                                    provenance="embedded_image_ocr",
                                )
                                page_blocks.append(img_block)
                                all_blocks.append(img_block)
                                global_reading_order += 1
                            continue

                        try:
                            base_img = doc.extract_image(xref)
                            w = int(base_img.get("width") or 0)
                            h = int(base_img.get("height") or 0)
                            # Filter out tiny icons, borders or bullets (< 60px or < 4000 total pixels)
                            if w >= 60 and h >= 60 and (w * h) >= 4000:
                                img_bytes = base_img["image"]
                                if hasattr(self.ocr_router.adapter, "extract_text_sync"):
                                    extracted_img_text, conf = self.ocr_router.adapter.extract_text_sync(img_bytes, options)
                                elif hasattr(self.ocr_router.adapter, "_sync_extract"):
                                    extracted_img_text, conf = self.ocr_router.adapter._sync_extract(img_bytes, options or {})
                                else:
                                    extracted_img_text, conf = "", 0.0

                                clean_ocr = extracted_img_text.replace("\x00", "").strip()
                                if clean_ocr:
                                    formatted_img_text = f"\n> **[Image Extracted Text (OCR)]**\n> {clean_ocr}\n"
                                    seen_image_ocr[xref] = formatted_img_text
                                    img_block = CanonicalBlock(
                                        block_id=self._generate_block_id(page_num, len(page_blocks)),
                                        block_type=BlockType.PARAGRAPH,
                                        text=formatted_img_text,
                                        reading_order=global_reading_order,
                                        page_number=page_num,
                                        confidence=conf,
                                        extraction_engine=f"ocr_embedded_{self.ocr_router.adapter.name}",
                                        provenance="embedded_image_ocr",
                                    )
                                    page_blocks.append(img_block)
                                    all_blocks.append(img_block)
                                    global_reading_order += 1
                                else:
                                    seen_image_ocr[xref] = ""
                            else:
                                seen_image_ocr[xref] = ""
                        except Exception as exc:
                            seen_image_ocr[xref] = ""
                            logger.debug(f"Embedded image OCR skipped for xref {xref}: {exc}")

                # 4. Image Asset Extraction (Optional)
                if extract_images and assets_dir:
                    assets_path = Path(assets_dir)
                    assets_path.mkdir(parents=True, exist_ok=True)
                    for img_index, img_info in enumerate(image_list):
                        xref = img_info[0]
                        try:
                            base_img = doc.extract_image(xref)
                            img_bytes = base_img["image"]
                            img_ext = base_img["ext"]
                            img_filename = f"page_{page_num}_img_{img_index + 1}.{img_ext}"
                            out_img_path = assets_path / img_filename
                            out_img_path.write_bytes(img_bytes)

                            img_block = CanonicalBlock(
                                block_id=self._generate_block_id(page_num, len(page_blocks)),
                                block_type=BlockType.IMAGE_REFERENCE,
                                text=f"[Image: {img_filename}]",
                                reading_order=global_reading_order,
                                page_number=page_num,
                                confidence=1.0,
                                extraction_engine=self.engine_name,
                                provenance="native_image",
                                metadata={
                                    "image_file": img_filename,
                                    "xref": xref,
                                    "width": base_img.get("width"),
                                    "height": base_img.get("height"),
                                    "format": img_ext,
                                },
                            )
                            page_blocks.append(img_block)
                            all_blocks.append(img_block)
                            global_reading_order += 1
                        except Exception as exc:
                            warnings.append(
                                f"Page {page_num}: Failed to extract image {xref}: {exc}"
                            )

                pages.append(
                    CanonicalPage(
                        page_number=page_num,
                        width=width,
                        height=height,
                        rotation=rotation,
                        is_scanned=is_scanned,
                        ocr_applied=ocr_applied,
                        blocks=page_blocks,
                        metadata={
                            "digital_char_count": total_page_digital_chars,
                            "image_count": len(image_list),
                            "table_count": len(extracted_table_rects),
                        },
                    )
                )

            status = (
                ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED
            )

            return CanonicalDocument(
                document_id=doc_id,
                original_filename=original_filename,
                detected_format="pdf",
                extraction_status=status,
                metadata=cleaned_metadata,
                page_count=page_count,
                extraction_engine=self.engine_name,
                extraction_version=self.version,
                created_at=datetime.now(UTC).isoformat(),
                pages=pages,
                blocks=all_blocks,
                warnings=warnings,
                errors=errors,
            )
        finally:
            doc.close()

    def _sort_blocks_reading_order(self, blocks: list[Any], page_width: float) -> list[Any]:
        """Sort blocks considering multi-column (2-column, 3-column) or single-column layout structure.

        Separates full-width spanning blocks (titles, banners, footers) from localized column flows.
        """
        if not blocks:
            return []

        midpoint = page_width / 2.0
        left_col: list[Any] = []
        right_col: list[Any] = []
        spanning: list[Any] = []

        for b in blocks:
            x0, y0, x1, y1 = b[:4]
            block_width = x1 - x0

            # If block occupies more than 60% of page width, it's a spanning element
            if block_width > page_width * 0.60:
                spanning.append(b)
            elif x1 <= midpoint + (page_width * 0.08):
                left_col.append(b)
            elif x0 >= midpoint - (page_width * 0.08):
                right_col.append(b)
            else:
                spanning.append(b)

        # Multi-column heuristic: both columns must have text elements
        if len(left_col) >= 1 and len(right_col) >= 1:
            left_col.sort(key=lambda b: (round(b[1], -1), b[0]))
            right_col.sort(key=lambda b: (round(b[1], -1), b[0]))

            # Top of columns and bottom of columns
            col_top_y = min(left_col[0][1], right_col[0][1])
            col_bottom_y = max(left_col[-1][3], right_col[-1][3])

            header_spanning = [b for b in spanning if b[3] <= col_top_y + 10]
            footer_spanning = [b for b in spanning if b[1] >= col_bottom_y - 10]
            mid_spanning = [
                b for b in spanning if b not in header_spanning and b not in footer_spanning
            ]

            header_spanning.sort(key=lambda b: (round(b[1], -1), b[0]))
            mid_spanning.sort(key=lambda b: (round(b[1], -1), b[0]))
            footer_spanning.sort(key=lambda b: (round(b[1], -1), b[0]))

            return header_spanning + left_col + mid_spanning + right_col + footer_spanning

        return sorted(blocks, key=lambda b: (round(b[1], -1), b[0]))

    def _format_table_text(self, grid: list[list[Any]]) -> str:
        """Render a table grid as clean Markdown-compatible text."""
        if not grid:
            return ""
        lines: list[str] = []
        for row in grid:
            cells = [str(c if c is not None else "").replace("\x00", "").replace("\n", " ").strip() for c in row]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    def _classify_text_block(self, text: str, height: float) -> BlockType:
        """Classify block into semantic type based on length, height and patterns."""
        stripped = text.strip()
        if stripped.startswith(("- ", "* ", "• ", "1. ", "2. ", "3. ")):
            return BlockType.LIST_ITEM
        if len(stripped) < 80 and not stripped.endswith((".", ":", ";")) and height > 16:
            return BlockType.HEADING
        return BlockType.PARAGRAPH
