"""ODP OpenDocument Presentation native intelligence adapter using secure defusedxml."""

import hashlib
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET

from app.modules.presentation_intelligence.adapters.base import BasePresentationAdapter
from app.modules.presentation_intelligence.schemas.presentation_document import (
    Element,
    ElementDimensions,
    ElementPosition,
    ElementType,
    PresentationDimensions,
    PresentationDocument,
    PresentationMetadata,
    Slide,
    SlideAsset,
    SlideParagraph,
    SlideTable,
    SlideTableCell,
    SlideTextRun,
    SpeakerNoteSummary,
)

MAX_ZIP_ENTRIES = 10_000
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "presentation": "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0",
    "svg": "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "dc": "http://purl.org/dc/elements/1.1/",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
}


def _parse_dimension(val: str | None, default: float = 0.0) -> float:
    """Parse ODF dimension strings like '10.5cm', '254mm', '10in' into inches."""
    if not val:
        return default
    val_clean = val.strip().lower()
    try:
        if val_clean.endswith("cm"):
            return float(val_clean[:-2]) / 2.54
        if val_clean.endswith("mm"):
            return float(val_clean[:-2]) / 25.4
        if val_clean.endswith("in"):
            return float(val_clean[:-2])
        if val_clean.endswith("pt"):
            return float(val_clean[:-2]) / 72.0
        return float(val_clean)
    except Exception:
        return default


class ODPPresentationAdapter(BasePresentationAdapter):
    """Native OpenDocument Presentation (.odp) adapter with strict XML security."""

    def __init__(self) -> None:
        super().__init__(format_id="odp")

    def can_handle(self, format_id: str) -> bool:
        return format_id.lower() in ("odp",)

    def _verify_archive_safety(self, file_path: Path) -> list[str]:
        warnings: list[str] = []
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                infolist = zf.infolist()
                if len(infolist) > MAX_ZIP_ENTRIES:
                    raise ValueError(f"ODP archive entry count exceeds limit ({len(infolist)})")

                total_bytes = 0
                for info in infolist:
                    if info.filename.startswith("/") or ".." in info.filename:
                        warnings.append(f"Suspicious path in ODP package: '{info.filename}'")
                    total_bytes += info.file_size
                    if total_bytes > MAX_UNCOMPRESSED_BYTES:
                        raise ValueError(f"ODP decompressed size exceeds limit ({MAX_UNCOMPRESSED_BYTES})")
        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid or corrupted ODP ZIP container: {e}") from e
        return warnings

    async def extract_presentation(
        self,
        file_path: Path,
        document_id: str,
        file_id: str,
        original_filename: str | None = None,
        max_slides: int = 500,
        options: dict[str, Any] | None = None,
    ) -> tuple[PresentationDocument, list[dict[str, Any]]]:
        """Extract slides, text boxes, tables, images, and speaker notes from ODP."""
        options = options or {}
        warnings: list[str] = self._verify_archive_safety(file_path)

        slides: list[Slide] = []
        doc_assets: list[SlideAsset] = []
        doc_tables: list[SlideTable] = []
        doc_notes: list[SpeakerNoteSummary] = []
        raw_assets_to_save: list[dict[str, Any]] = []

        title: str | None = None
        author: str | None = None
        created_at_str: str | None = None
        modified_at_str: str | None = None
        language: str | None = None

        with zipfile.ZipFile(file_path, "r") as zf:
            file_names = zf.namelist()

            # 1. Parse meta.xml
            if "meta.xml" in file_names:
                try:
                    meta_bytes = zf.read("meta.xml")
                    meta_root = ET.fromstring(meta_bytes)
                    title_elem = meta_root.find(".//dc:title", NS)
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()

                    creator_elem = meta_root.find(".//dc:creator", NS)
                    if creator_elem is not None and creator_elem.text:
                        author = creator_elem.text.strip()

                    date_elem = meta_root.find(".//dc:date", NS)
                    if date_elem is not None and date_elem.text:
                        modified_at_str = date_elem.text.strip()

                    created_elem = meta_root.find(".//meta:creation-date", NS)
                    if created_elem is not None and created_elem.text:
                        created_at_str = created_elem.text.strip()

                    lang_elem = meta_root.find(".//dc:language", NS)
                    if lang_elem is not None and lang_elem.text:
                        language = lang_elem.text.strip()
                except Exception as e:
                    warnings.append(f"Failed parsing ODP meta.xml: {e}")

            # 2. Parse content.xml
            if "content.xml" not in file_names:
                raise ValueError("Missing 'content.xml' in ODP package.")

            content_bytes = zf.read("content.xml")
            root = ET.fromstring(content_bytes)

            pages = root.findall(".//draw:page", NS)
            if not pages:
                warnings.append("No <draw:page> slide elements found in ODP presentation.")

            asset_counter = 0

            for page_idx, page in enumerate(pages[:max_slides], start=1):
                slide_id = f"odp_slide_{page_idx}"
                page_name = page.attrib.get(f"{{{NS['draw']}}}name", f"Slide {page_idx}")

                slide_title: str | None = None
                elements: list[Element] = []
                speaker_notes_text: str | None = None

                # Check for Speaker Notes (<presentation:notes>)
                notes_elem = page.find(".//presentation:notes", NS)
                if notes_elem is not None:
                    note_paragraphs = []
                    for np in notes_elem.findall(".//text:p", NS):
                        if np.text and np.text.strip():
                            note_paragraphs.append(np.text.strip())
                    if note_paragraphs:
                        speaker_notes_text = "\n".join(note_paragraphs)
                        doc_notes.append(
                            SpeakerNoteSummary(
                                slide_id=slide_id,
                                slide_number=page_idx,
                                text=speaker_notes_text,
                                word_count=len(speaker_notes_text.split()),
                            )
                        )

                # Process Frames (<draw:frame>)
                frames = page.findall(".//draw:frame", NS)
                for f_idx, frame in enumerate(frames, start=1):
                    # Check if this frame is inside notes; if so, skip visible elements
                    is_inside_notes = False
                    # We only care about frames directly on page or in shapes, not inside presentation:notes
                    for n in page.findall(".//presentation:notes//draw:frame", NS):
                        if n == frame:
                            is_inside_notes = True
                            break
                    if is_inside_notes:
                        continue

                    elem_id = f"{slide_id}_elem_{f_idx}"
                    x_in = _parse_dimension(frame.attrib.get(f"{{{NS['svg']}}}x"))
                    y_in = _parse_dimension(frame.attrib.get(f"{{{NS['svg']}}}y"))
                    w_in = _parse_dimension(frame.attrib.get(f"{{{NS['svg']}}}width"))
                    h_in = _parse_dimension(frame.attrib.get(f"{{{NS['svg']}}}height"))
                    pos = ElementPosition(left=round(x_in, 2), top=round(y_in, 2))
                    dims = ElementDimensions(width=round(w_in, 2), height=round(h_in, 2))

                    # 1. Image
                    image_elem = frame.find(".//draw:image", NS)
                    if image_elem is not None:
                        href = image_elem.attrib.get(f"{{{NS['xlink']}}}href", "")
                        if href and not href.startswith("http"):
                            img_path_in_zip = href.lstrip("/")
                            if img_path_in_zip in file_names:
                                img_data = zf.read(img_path_in_zip)
                                sha256_hash = hashlib.sha256(img_data).hexdigest()
                                ext = img_path_in_zip.split(".")[-1].lower() if "." in img_path_in_zip else "png"
                                asset_counter += 1
                                asset_id = f"odp_asset_{page_idx}_{asset_counter}"

                                slide_asset = SlideAsset(
                                    asset_id=asset_id,
                                    slide_id=slide_id,
                                    slide_number=page_idx,
                                    original_filename=img_path_in_zip.split("/")[-1],
                                    format=ext,
                                    content_type=f"image/{ext}",
                                    sha256=sha256_hash,
                                    size_bytes=len(img_data),
                                    position=pos,
                                    dimensions=dims,
                                )
                                doc_assets.append(slide_asset)
                                raw_assets_to_save.append({
                                    "asset_id": asset_id,
                                    "sha256": sha256_hash,
                                    "blob": img_data,
                                    "format": ext,
                                    "content_type": f"image/{ext}",
                                    "slide_number": page_idx,
                                })

                                elements.append(
                                    Element(
                                        element_id=elem_id,
                                        element_type=ElementType.IMAGE,
                                        text=f"[Image: {img_path_in_zip.split('/')[-1]}]",
                                        position=pos,
                                        dimensions=dims,
                                        asset_reference=asset_id,
                                    )
                                )
                                continue

                    # 2. Table
                    table_elem = frame.find(".//table:table", NS)
                    if table_elem is not None:
                        table_rows: list[list[SlideTableCell]] = []
                        table_headers: list[str] = []
                        for r_idx, r_elem in enumerate(table_elem.findall(".//table:table-row", NS)):
                            cell_row: list[SlideTableCell] = []
                            for c_idx, c_elem in enumerate(r_elem.findall(".//table:table-cell", NS)):
                                cell_text = " ".join(
                                    t.text.strip()
                                    for t in c_elem.findall(".//text:p", NS)
                                    if t.text and t.text.strip()
                                )
                                is_hdr = r_idx == 0
                                if is_hdr:
                                    table_headers.append(cell_text)
                                cell_row.append(
                                    SlideTableCell(
                                        row=r_idx,
                                        column=c_idx,
                                        text=cell_text,
                                        is_header=is_hdr,
                                    )
                                )
                            table_rows.append(cell_row)

                        if table_rows:
                            tbl_id = f"{slide_id}_tbl_{len(doc_tables) + 1}"
                            slide_table = SlideTable(
                                table_id=tbl_id,
                                slide_id=slide_id,
                                slide_number=page_idx,
                                rows_count=len(table_rows),
                                columns_count=len(table_rows[0]) if table_rows else 0,
                                headers=table_headers,
                                rows=table_rows,
                                has_header=len(table_headers) > 0,
                            )
                            doc_tables.append(slide_table)

                            elements.append(
                                Element(
                                    element_id=elem_id,
                                    element_type=ElementType.TABLE,
                                    text=f"[Table: {len(table_rows)} rows x {len(table_rows[0]) if table_rows else 0} cols]",
                                    position=pos,
                                    dimensions=dims,
                                    raw_data=slide_table.model_dump(),
                                )
                            )
                            continue

                    # 3. Text Box (<draw:text-box>)
                    text_box = frame.find(".//draw:text-box", NS)
                    if text_box is not None:
                        paragraphs: list[SlideParagraph] = []
                        text_lines: list[str] = []

                        # Extract plain paragraphs
                        for p in text_box.findall("./text:p", NS):
                            p_txt = "".join(p.itertext()).strip()
                            if p_txt:
                                text_lines.append(p_txt)
                                paragraphs.append(
                                    SlideParagraph(
                                        text=p_txt,
                                        level=0,
                                        bullet=False,
                                        runs=[SlideTextRun(text=p_txt)],
                                    )
                                )

                        # Extract lists (<text:list> and nested items)
                        def _extract_list(
                            list_elem: Any,
                            level: int,
                            target_lines: list[str],
                            target_paras: list[SlideParagraph],
                        ) -> None:
                            for item in list_elem.findall("./text:list-item", NS):
                                for item_p in item.findall("./text:p", NS):
                                    item_txt = "".join(item_p.itertext()).strip()
                                    if item_txt:
                                        target_lines.append(item_txt)
                                        target_paras.append(
                                            SlideParagraph(
                                                text=item_txt,
                                                level=level,
                                                bullet=True,
                                                runs=[SlideTextRun(text=item_txt)],
                                            )
                                        )
                                # Nested sub-lists
                                for sub_list in item.findall("./text:list", NS):
                                    _extract_list(sub_list, level + 1, target_lines, target_paras)

                        for l_elem in text_box.findall("./text:list", NS):
                            _extract_list(l_elem, 1, text_lines, paragraphs)

                        if text_lines:
                            is_title = (
                                not slide_title
                                and ("title" in frame.attrib.get(f"{{{NS['presentation']}}}class", "").lower()
                                     or f_idx == 1)
                            )
                            if is_title:
                                slide_title = "\n".join(text_lines)

                            elements.append(
                                Element(
                                    element_id=elem_id,
                                    element_type=ElementType.TITLE if is_title else ElementType.TEXT,
                                    text="\n".join(text_lines),
                                    paragraphs=paragraphs,
                                    position=pos,
                                    dimensions=dims,
                                )
                            )
                            continue

                # Slide Reading Order
                reading_sorted = sorted(
                    elements,
                    key=lambda e: (e.position.top, e.position.left),
                )
                reading_order = [e.element_id for e in reading_sorted]

                slides.append(
                    Slide(
                        slide_id=slide_id,
                        slide_number=page_idx,
                        title=slide_title or page_name,
                        elements=elements,
                        speaker_notes=speaker_notes_text,
                        hidden=False,
                        reading_order=reading_order,
                    )
                )

        dimensions = PresentationDimensions(
            width=10.0,
            height=7.5,
            aspect_ratio="4:3",
            unit="inches",
        )

        metadata = PresentationMetadata(
            title=title or (original_filename if original_filename else None),
            author=author,
            created_at=created_at_str,
            modified_at=modified_at_str,
            language=language,
            slide_count=len(slides),
            hidden_slide_count=0,
            presentation_dimensions=dimensions,
            embedded_media_count=len(doc_assets),
        )

        doc = PresentationDocument(
            document_id=document_id,
            file_id=file_id,
            format="odp",
            metadata=metadata,
            presentation_dimensions=dimensions,
            slide_count=len(slides),
            slides=slides,
            assets=doc_assets,
            charts=[],
            tables=doc_tables,
            diagrams=[],
            speaker_notes=doc_notes,
            extraction_metadata={
                "engine_name": "odf-defusedxml",
                "engine_version": "1.0.0",
                "extracted_at": datetime.now(UTC).isoformat(),
            },
            warnings=warnings,
            confidence=0.95,
            processing_status="completed",
        )

        return doc, raw_assets_to_save
