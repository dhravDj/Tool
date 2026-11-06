"""PPTX presentation intelligence adapter using python-pptx and secure XML guards."""

import hashlib
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from app.modules.presentation_intelligence.adapters.base import BasePresentationAdapter
from app.modules.presentation_intelligence.charts.chart_extractor import (
    PresentationChartExtractor,
)
from app.modules.presentation_intelligence.diagrams.diagram_extractor import (
    PresentationDiagramExtractor,
)
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
    SlideChart,
    SlideDiagram,
    SlideParagraph,
    SlideTable,
    SlideTableCell,
    SlideTextRun,
    SpeakerNoteSummary,
)

MAX_ZIP_ENTRIES = 10_000
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MB


class PPTXPresentationAdapter(BasePresentationAdapter):
    """Adapter for modern PowerPoint Open XML (.pptx) presentations."""

    def __init__(self) -> None:
        super().__init__(format_id="pptx")

    def can_handle(self, format_id: str) -> bool:
        return format_id.lower() in ("pptx",)

    def _verify_archive_safety(self, file_path: Path) -> list[str]:
        """Verify ZIP archive integrity and guard against zip bombs and path traversal."""
        warnings: list[str] = []
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                infolist = zf.infolist()
                if len(infolist) > MAX_ZIP_ENTRIES:
                    raise ValueError(
                        f"Archive exceeds maximum allowed entries ({len(infolist)} > {MAX_ZIP_ENTRIES})"
                    )

                total_size = 0
                for info in infolist:
                    # Path traversal check
                    if info.filename.startswith("/") or ".." in info.filename:
                        warnings.append(f"Suspicious path in ZIP entry: '{info.filename}'")

                    total_size += info.file_size
                    if total_size > MAX_UNCOMPRESSED_BYTES:
                        raise ValueError(
                            f"Archive exceeds maximum decompressed size limit ({MAX_UNCOMPRESSED_BYTES} bytes)"
                        )

                    if info.compress_size > 0 and (info.file_size / info.compress_size > 150):
                        warnings.append(f"High compression ratio on '{info.filename}'")
        except zipfile.BadZipFile as e:
            raise ValueError(f"Corrupted or invalid PPTX ZIP package: {e}") from e
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
        """Extract slide hierarchy, text runs, tables, charts, images, and notes from PPTX."""
        options = options or {}
        warnings: list[str] = []

        archive_warnings = self._verify_archive_safety(file_path)
        warnings.extend(archive_warnings)

        prs = Presentation(str(file_path))

        # Presentation Dimensions
        try:
            width_in = float(prs.slide_width.inches) if prs.slide_width is not None else 10.0
            height_in = float(prs.slide_height.inches) if prs.slide_height is not None else 7.5
        except Exception:
            width_in, height_in = 10.0, 7.5

        ratio_val = round(width_in / height_in, 2) if height_in > 0 else 1.33
        aspect_ratio = "16:9" if abs(ratio_val - 1.78) < 0.15 else "4:3"
        dimensions = PresentationDimensions(
            width=round(width_in, 2),
            height=round(height_in, 2),
            aspect_ratio=aspect_ratio,
            unit="inches",
        )

        # Core Properties / Metadata
        props = prs.core_properties
        title = getattr(props, "title", None) or None
        subject = getattr(props, "subject", None) or None
        author = getattr(props, "author", None) or None
        created_at_dt = getattr(props, "created", None)
        modified_at_dt = getattr(props, "modified", None)
        created_at_str = created_at_dt.isoformat() if created_at_dt else None
        modified_at_str = modified_at_dt.isoformat() if modified_at_dt else None
        language = getattr(props, "language", None) or None

        layout_names = [layout.name for layout in prs.slide_layouts if hasattr(layout, "name")]

        total_slides = len(prs.slides)
        if total_slides > max_slides:
            warnings.append(
                f"Presentation has {total_slides} slides; capped processing at {max_slides}."
            )

        slides: list[Slide] = []
        doc_assets: list[SlideAsset] = []
        doc_charts: list[SlideChart] = []
        doc_tables: list[SlideTable] = []
        doc_diagrams: list[SlideDiagram] = []
        doc_notes: list[SpeakerNoteSummary] = []
        raw_assets_to_save: list[dict[str, Any]] = []

        hidden_slides_count = 0
        asset_counter = 0

        for slide_idx, slide in enumerate(prs.slides, start=1):
            if slide_idx > max_slides:
                break
            slide_id = f"slide_{slide_idx}_{getattr(slide, 'slide_id', slide_idx)}"

            # Hidden slide detection
            is_hidden = False
            try:
                xml_attrib = slide.element.attrib
                if xml_attrib.get("show") == "0":
                    is_hidden = True
            except Exception:
                pass
            if is_hidden:
                hidden_slides_count += 1

            # Slide title
            slide_title = None
            try:
                if slide.shapes.title and slide.shapes.title.has_text_frame:
                    slide_title = slide.shapes.title.text.strip() or None
            except Exception:
                pass

            # Speaker notes
            speaker_notes_text: str | None = None
            try:
                if slide.has_notes_slide and slide.notes_slide:
                    notes_tf = slide.notes_slide.notes_text_frame
                    if notes_tf:
                        txt = notes_tf.text.strip()
                        if txt:
                            speaker_notes_text = txt
                            doc_notes.append(
                                SpeakerNoteSummary(
                                    slide_id=slide_id,
                                    slide_number=slide_idx,
                                    text=txt,
                                    word_count=len(txt.split()),
                                )
                            )
            except Exception as e:
                warnings.append(f"Slide {slide_idx}: Failed to extract speaker notes: {e}")

            # Extract shapes & elements
            elements: list[Element] = []
            slide_shapes_list = list(slide.shapes)

            for shape_idx, shape in enumerate(slide_shapes_list, start=1):
                elem_id = f"{slide_id}_elem_{shape_idx}"
                shape_left = float(getattr(shape, "left", 0)) / 914400.0
                shape_top = float(getattr(shape, "top", 0)) / 914400.0
                shape_width = float(getattr(shape, "width", 0)) / 914400.0
                shape_height = float(getattr(shape, "height", 0)) / 914400.0
                pos = ElementPosition(left=round(shape_left, 2), top=round(shape_top, 2))
                dims = ElementDimensions(width=round(shape_width, 2), height=round(shape_height, 2))

                shape_type = getattr(shape, "shape_type", None)

                # 1. Native Table
                if getattr(shape, "has_table", False):
                    try:
                        table = shape.table
                        rows_data: list[list[SlideTableCell]] = []
                        headers: list[str] = []

                        for r_idx, row in enumerate(table.rows):
                            row_cells: list[SlideTableCell] = []
                            for c_idx, cell in enumerate(row.cells):
                                c_text = cell.text.strip()
                                is_hdr = r_idx == 0
                                if is_hdr:
                                    headers.append(c_text)
                                row_cells.append(
                                    SlideTableCell(
                                        row=r_idx,
                                        column=c_idx,
                                        text=c_text,
                                        is_header=is_hdr,
                                    )
                                )
                            rows_data.append(row_cells)

                        tbl_id = f"{slide_id}_tbl_{len(doc_tables) + 1}"
                        slide_table = SlideTable(
                            table_id=tbl_id,
                            slide_id=slide_id,
                            slide_number=slide_idx,
                            rows_count=len(table.rows),
                            columns_count=len(table.columns),
                            headers=headers,
                            rows=rows_data,
                            has_header=len(headers) > 0,
                        )
                        doc_tables.append(slide_table)

                        elements.append(
                            Element(
                                element_id=elem_id,
                                element_type=ElementType.TABLE,
                                text=f"[Table: {len(table.rows)} rows x {len(table.columns)} cols]",
                                position=pos,
                                dimensions=dims,
                                source_provenance={
                                    "shape_id": getattr(shape, "shape_id", shape_idx),
                                    "shape_name": getattr(shape, "name", "Table"),
                                },
                                raw_data=slide_table.model_dump(),
                            )
                        )
                    except Exception as e:
                        warnings.append(f"Slide {slide_idx}: Failed to extract table: {e}")
                    continue

                # 2. Native Chart
                if getattr(shape, "has_chart", False):
                    try:
                        extracted_chart = PresentationChartExtractor.extract_pptx_chart(
                            shape=shape,
                            slide_id=slide_id,
                            slide_number=slide_idx,
                            chart_counter=len(doc_charts) + 1,
                        )
                        doc_charts.append(extracted_chart)

                        elements.append(
                            Element(
                                element_id=elem_id,
                                element_type=ElementType.CHART,
                                text=f"[Chart: {extracted_chart.chart_type.value} - {extracted_chart.title or 'Untitled'}]",
                                position=pos,
                                dimensions=dims,
                                source_provenance={
                                    "shape_id": getattr(shape, "shape_id", shape_idx),
                                    "shape_name": getattr(shape, "name", "Chart"),
                                },
                                raw_data=extracted_chart.model_dump(),
                            )
                        )
                    except Exception as e:
                        warnings.append(f"Slide {slide_idx}: Failed to extract chart: {e}")
                    continue

                # 3. Image / Picture
                if (
                    shape_type == MSO_SHAPE_TYPE.PICTURE
                    or hasattr(shape, "image")
                ):
                    try:
                        image = shape.image
                        blob = image.blob
                        sha256_hash = hashlib.sha256(blob).hexdigest()
                        fmt = getattr(image, "ext", "png").lower()
                        content_type = getattr(image, "content_type", f"image/{fmt}")

                        asset_counter += 1
                        asset_id = f"asset_{slide_idx}_{asset_counter}"

                        alt_text = None
                        try:
                            alt_text = shape.element.xpath(".//p:cNvPr/@descr")
                            alt_text = alt_text[0] if alt_text else getattr(shape, "name", None)
                        except Exception:
                            alt_text = getattr(shape, "name", None)

                        slide_asset = SlideAsset(
                            asset_id=asset_id,
                            slide_id=slide_id,
                            slide_number=slide_idx,
                            original_filename=getattr(image, "filename", f"image_{asset_counter}.{fmt}"),
                            format=fmt,
                            content_type=content_type,
                            sha256=sha256_hash,
                            size_bytes=len(blob),
                            position=pos,
                            dimensions=dims,
                            alt_text=alt_text,
                        )
                        doc_assets.append(slide_asset)
                        raw_assets_to_save.append({
                            "asset_id": asset_id,
                            "sha256": sha256_hash,
                            "blob": blob,
                            "format": fmt,
                            "content_type": content_type,
                            "slide_number": slide_idx,
                        })

                        elements.append(
                            Element(
                                element_id=elem_id,
                                element_type=ElementType.IMAGE,
                                text=f"[Image: {alt_text or fmt}]",
                                position=pos,
                                dimensions=dims,
                                asset_reference=asset_id,
                                source_provenance={
                                    "shape_id": getattr(shape, "shape_id", shape_idx),
                                    "shape_name": getattr(shape, "name", "Picture"),
                                },
                            )
                        )
                    except Exception as e:
                        warnings.append(f"Slide {slide_idx}: Failed to extract picture: {e}")
                    continue

                # 4. Grouped Shapes
                if shape_type == MSO_SHAPE_TYPE.GROUP:
                    try:
                        child_elements: list[dict[str, Any]] = []
                        if hasattr(shape, "shapes"):
                            for c_shape in shape.shapes:
                                c_text = ""
                                if getattr(c_shape, "has_text_frame", False) and c_shape.text_frame:
                                    c_text = c_shape.text_frame.text.strip()
                                child_elements.append({
                                    "shape_id": getattr(c_shape, "shape_id", ""),
                                    "name": getattr(c_shape, "name", ""),
                                    "text": c_text,
                                })
                        elements.append(
                            Element(
                                element_id=elem_id,
                                element_type=ElementType.GROUP,
                                text=f"[Group with {len(child_elements)} shapes]",
                                position=pos,
                                dimensions=dims,
                                source_provenance={
                                    "shape_id": getattr(shape, "shape_id", shape_idx),
                                    "shape_name": getattr(shape, "name", "Group"),
                                },
                                relationships=child_elements,
                            )
                        )
                    except Exception as e:
                        warnings.append(f"Slide {slide_idx}: Failed to extract group shape: {e}")
                    continue

                # 5. Text Frames, Titles & General Shapes with Text
                if getattr(shape, "has_text_frame", False) and shape.text_frame:
                    try:
                        tf = shape.text_frame
                        paragraphs: list[SlideParagraph] = []
                        full_text_parts: list[str] = []

                        for p in tf.paragraphs:
                            p_text = p.text.strip()
                            if not p_text:
                                continue
                            full_text_parts.append(p_text)

                            level = getattr(p, "level", 0)
                            bullet = level > 0 or getattr(p, "is_bullet", False)
                            align_str = None
                            if hasattr(p, "alignment") and p.alignment is not None:
                                align_str = str(p.alignment.name).lower() if hasattr(p.alignment, "name") else str(p.alignment)

                            runs: list[SlideTextRun] = []
                            for r in p.runs:
                                r_text = r.text
                                if not r_text:
                                    continue
                                font = r.font
                                font_size_pt = font.size.pt if getattr(font, "size", None) else None
                                runs.append(
                                    SlideTextRun(
                                        text=r_text,
                                        font_name=getattr(font, "name", None),
                                        font_size=font_size_pt,
                                        bold=bool(getattr(font, "bold", False)),
                                        italic=bool(getattr(font, "italic", False)),
                                        underline=bool(getattr(font, "underline", False)),
                                    )
                                )

                            paragraphs.append(
                                SlideParagraph(
                                    text=p_text,
                                    level=level,
                                    bullet=bullet,
                                    alignment=align_str,
                                    runs=runs,
                                )
                            )

                        if full_text_parts:
                            is_title = shape == getattr(slide.shapes, "title", None)
                            elem_type = ElementType.TITLE if is_title else ElementType.TEXT
                            if is_title and not slide_title:
                                slide_title = "\n".join(full_text_parts)

                            elements.append(
                                Element(
                                    element_id=elem_id,
                                    element_type=elem_type,
                                    text="\n".join(full_text_parts),
                                    paragraphs=paragraphs,
                                    position=pos,
                                    dimensions=dims,
                                    source_provenance={
                                        "shape_id": getattr(shape, "shape_id", shape_idx),
                                        "shape_name": getattr(shape, "name", "TextBox"),
                                    },
                                )
                            )
                    except Exception as e:
                        warnings.append(f"Slide {slide_idx}: Failed to extract text frame: {e}")
                    continue

                # 6. Fallback Shape / Line / Connector
                shape_name = getattr(shape, "name", "Shape")
                elem_type = ElementType.CONNECTOR if "CONNECTOR" in str(shape_type) or "LINE" in str(shape_type) else ElementType.SHAPE
                elements.append(
                    Element(
                        element_id=elem_id,
                        element_type=elem_type,
                        text=f"[{shape_name}]",
                        position=pos,
                        dimensions=dims,
                        source_provenance={
                            "shape_id": getattr(shape, "shape_id", shape_idx),
                            "shape_name": shape_name,
                        },
                    )
                )

            # Slide Reading Order: sort element IDs top-to-bottom, left-to-right
            reading_sorted = sorted(
                elements,
                key=lambda e: (e.position.top, e.position.left),
            )
            reading_order = [e.element_id for e in reading_sorted]

            # Diagram Extraction on slide
            try:
                slide_diag = PresentationDiagramExtractor.extract_slide_diagram(
                    slide_id=slide_id,
                    slide_number=slide_idx,
                    shapes=slide_shapes_list,
                    diagram_counter=len(doc_diagrams) + 1,
                )
                if slide_diag:
                    doc_diagrams.append(slide_diag)
            except Exception as e:
                warnings.append(f"Slide {slide_idx}: Failed to extract diagram: {e}")

            slides.append(
                Slide(
                    slide_id=slide_id,
                    slide_number=slide_idx,
                    title=slide_title,
                    dimensions=dims,
                    elements=elements,
                    speaker_notes=speaker_notes_text,
                    hidden=is_hidden,
                    reading_order=reading_order,
                )
            )

        metadata = PresentationMetadata(
            title=title or (original_filename if original_filename else None),
            subject=subject,
            author=author,
            created_at=created_at_str,
            modified_at=modified_at_str,
            language=language,
            slide_count=len(slides),
            hidden_slide_count=hidden_slides_count,
            presentation_dimensions=dimensions,
            layout_names=layout_names[:20],
            embedded_media_count=len(doc_assets),
        )

        doc = PresentationDocument(
            document_id=document_id,
            file_id=file_id,
            format="pptx",
            metadata=metadata,
            presentation_dimensions=dimensions,
            slide_count=len(slides),
            slides=slides,
            assets=doc_assets,
            charts=doc_charts,
            tables=doc_tables,
            diagrams=doc_diagrams,
            speaker_notes=doc_notes,
            extraction_metadata={
                "engine_name": "python-pptx",
                "engine_version": "1.0.2",
                "extracted_at": datetime.now(UTC).isoformat(),
            },
            warnings=warnings,
            confidence=1.0,
            processing_status="completed",
        )

        return doc, raw_assets_to_save
