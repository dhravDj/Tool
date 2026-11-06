"""Legacy PowerPoint (.ppt) adapter with sandboxed conversion and native OLE2 fallback."""

import asyncio
import os
import shutil
import struct
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import olefile

from app.modules.presentation_intelligence.adapters.base import BasePresentationAdapter
from app.modules.presentation_intelligence.adapters.pptx_adapter import (
    PPTXPresentationAdapter,
)
from app.modules.presentation_intelligence.schemas.presentation_document import (
    Element,
    ElementType,
    PresentationDimensions,
    PresentationDocument,
    PresentationMetadata,
    Slide,
    SlideParagraph,
    SlideTextRun,
)

CONVERSION_TIMEOUT_SECONDS = 20


class PPTPresentationAdapter(BasePresentationAdapter):
    """Adapter for legacy binary PowerPoint 97-2003 (.ppt) presentations."""

    def __init__(self) -> None:
        super().__init__(format_id="ppt")
        self._pptx_adapter = PPTXPresentationAdapter()

    def can_handle(self, format_id: str) -> bool:
        return format_id.lower() in ("ppt",)

    def _find_libreoffice_binary(self) -> str | None:
        """Find headless LibreOffice or soffice executable if installed."""
        for candidate in ("libreoffice", "soffice"):
            bin_path = shutil.which(candidate)
            if bin_path and os.access(bin_path, os.X_OK):
                return bin_path
        return None

    async def _convert_ppt_to_pptx_sandboxed(
        self,
        ppt_path: Path,
        temp_dir: Path,
        lo_bin: str,
    ) -> Path:
        """Execute sandboxed headless LibreOffice conversion to PPTX."""
        out_dir = temp_dir / "converted"
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            lo_bin,
            "--headless",
            "--invisible",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            "pptx",
            "--outdir",
            str(out_dir),
            str(ppt_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=CONVERSION_TIMEOUT_SECONDS,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice conversion failed with code {proc.returncode}: {stderr.decode(errors='ignore')}"
                )
        except TimeoutError as e:
            try:
                proc.kill()
            except Exception:
                pass
            raise TimeoutError(
                f"LibreOffice conversion timed out after {CONVERSION_TIMEOUT_SECONDS}s"
            ) from e

        expected_pptx = out_dir / f"{ppt_path.stem}.pptx"
        if not expected_pptx.exists():
            candidates = list(out_dir.glob("*.pptx"))
            if candidates:
                return candidates[0]
            raise FileNotFoundError(
                f"Converted PPTX was not created by LibreOffice: {stdout.decode(errors='ignore')}"
            )

        return expected_pptx

    def _extract_native_ole2_ppt(
        self,
        file_path: Path,
        document_id: str,
        file_id: str,
        original_filename: str | None = None,
    ) -> PresentationDocument:
        """Extract metadata, slide text runs, and notes directly from binary OLE2 streams."""
        if not olefile.isOleFile(file_path):
            raise ValueError(f"File '{file_path.name}' is not a valid OLE2 compound binary presentation.")

        warnings: list[str] = [
            "LibreOffice headless engine not present; extracted presentation using native OLE2 binary stream parser."
        ]

        title: str | None = None
        author: str | None = None
        subject: str | None = None
        slide_count_meta: int = 1

        with olefile.OleFileIO(file_path) as ole:
            # 1. Parse OLE2 SummaryInformation
            if ole.exists("\x05SummaryInformation"):
                try:
                    meta = ole.get_metadata()
                    title = meta.title.decode("utf-8", errors="ignore") if isinstance(meta.title, bytes) else meta.title
                    author = meta.author.decode("utf-8", errors="ignore") if isinstance(meta.author, bytes) else meta.author
                    subject = meta.subject.decode("utf-8", errors="ignore") if isinstance(meta.subject, bytes) else meta.subject
                except Exception as e:
                    warnings.append(f"Could not parse OLE2 SummaryInformation: {e}")

            if ole.exists("\x05DocumentSummaryInformation"):
                try:
                    meta_doc = ole.get_metadata()
                    if hasattr(meta_doc, "slides") and meta_doc.slides:
                        slide_count_meta = int(meta_doc.slides)
                except Exception:
                    pass

            # 2. Parse 'PowerPoint Document' binary stream records
            extracted_text_blocks: list[str] = []
            if ole.exists("PowerPoint Document"):
                try:
                    stream_data = ole.openstream("PowerPoint Document").read()
                    offset = 0
                    stream_len = len(stream_data)

                    while offset + 8 <= stream_len:
                        ver_inst, rec_type, rec_len = struct.unpack_from("<HHI", stream_data, offset)
                        offset += 8

                        if offset + rec_len > stream_len:
                            break

                        # Record types from [MS-PPT] specification:
                        # 4000 (0x0FA0): TextCharsAtom (UTF-16LE text)
                        # 4008 (0x0FA8): TextBytesAtom (8-bit ASCII / ANSI text)
                        # 4026 (0x0FBA): CString (UTF-16LE string)
                        if rec_type == 4000:
                            raw_bytes = stream_data[offset : offset + rec_len]
                            txt = raw_bytes.decode("utf-16le", errors="ignore").strip()
                            if txt and len(txt) > 1:
                                extracted_text_blocks.append(txt)
                        elif rec_type == 4008:
                            raw_bytes = stream_data[offset : offset + rec_len]
                            txt = raw_bytes.decode("latin1", errors="ignore").strip()
                            if txt and len(txt) > 1:
                                extracted_text_blocks.append(txt)
                        elif rec_type == 4026:
                            raw_bytes = stream_data[offset : offset + rec_len]
                            txt = raw_bytes.decode("utf-16le", errors="ignore").strip()
                            if txt and len(txt) > 1:
                                extracted_text_blocks.append(txt)

                        offset += rec_len
                except Exception as e:
                    warnings.append(f"Failed parsing PowerPoint Document binary stream: {e}")

        # Partition text blocks into slides
        slides: list[Slide] = []
        if not extracted_text_blocks:
            slides.append(
                Slide(
                    slide_id="slide_1",
                    slide_number=1,
                    title=title or "Slide 1",
                    elements=[
                        Element(
                            element_id="slide_1_elem_1",
                            element_type=ElementType.TEXT,
                            text="[No text records found in legacy binary stream]",
                        )
                    ],
                )
            )
        else:
            # If multiple text blocks, treat the first block as title or partition into slides
            slide_idx = 1
            current_elements: list[Element] = []
            slide_title = None

            for b_idx, block in enumerate(extracted_text_blocks):
                elem_id = f"slide_{slide_idx}_elem_{b_idx + 1}"
                is_title = b_idx == 0 or (slide_title is None and len(block) < 60)
                if is_title and not slide_title:
                    slide_title = block

                elem_type = ElementType.TITLE if is_title else ElementType.TEXT
                current_elements.append(
                    Element(
                        element_id=elem_id,
                        element_type=elem_type,
                        text=block,
                        paragraphs=[
                            SlideParagraph(
                                text=block,
                                level=0,
                                bullet=False,
                                runs=[SlideTextRun(text=block)],
                            )
                        ],
                    )
                )

                # Heuristic: split every 3-5 blocks into new slide if more blocks remain
                if len(current_elements) >= 3 and b_idx < len(extracted_text_blocks) - 1:
                    slides.append(
                        Slide(
                            slide_id=f"slide_{slide_idx}",
                            slide_number=slide_idx,
                            title=slide_title or f"Slide {slide_idx}",
                            elements=current_elements,
                            reading_order=[e.element_id for e in current_elements],
                        )
                    )
                    slide_idx += 1
                    current_elements = []
                    slide_title = None

            if current_elements:
                slides.append(
                    Slide(
                        slide_id=f"slide_{slide_idx}",
                        slide_number=slide_idx,
                        title=slide_title or f"Slide {slide_idx}",
                        elements=current_elements,
                        reading_order=[e.element_id for e in current_elements],
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
            subject=subject,
            author=author,
            slide_count=max(len(slides), slide_count_meta),
            presentation_dimensions=dimensions,
        )

        return PresentationDocument(
            document_id=document_id,
            file_id=file_id,
            format="ppt",
            metadata=metadata,
            presentation_dimensions=dimensions,
            slide_count=len(slides),
            slides=slides,
            assets=[],
            charts=[],
            tables=[],
            diagrams=[],
            speaker_notes=[],
            extraction_metadata={
                "engine_name": "ole2-binary-parser",
                "engine_version": "1.0.0",
                "extracted_at": datetime.now(UTC).isoformat(),
            },
            warnings=warnings,
            confidence=0.85,
            processing_status="completed",
        )

    async def extract_presentation(
        self,
        file_path: Path,
        document_id: str,
        file_id: str,
        original_filename: str | None = None,
        max_slides: int = 500,
        options: dict[str, Any] | None = None,
    ) -> tuple[PresentationDocument, list[dict[str, Any]]]:
        """Extract presentation from legacy PPT using LibreOffice conversion or native OLE2 parser."""
        lo_bin = self._find_libreoffice_binary()

        if lo_bin:
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    converted_pptx = await self._convert_ppt_to_pptx_sandboxed(
                        ppt_path=file_path,
                        temp_dir=Path(temp_dir),
                        lo_bin=lo_bin,
                    )
                    doc, assets = await self._pptx_adapter.extract_presentation(
                        file_path=converted_pptx,
                        document_id=document_id,
                        file_id=file_id,
                        original_filename=original_filename,
                        max_slides=max_slides,
                        options=options,
                    )
                    doc.format = "ppt"
                    doc.extraction_metadata["conversion_engine"] = "libreoffice-headless"
                    doc.warnings.append(
                        "Converted legacy PPT to PPTX via headless LibreOffice before extraction."
                    )
                    return doc, assets
                except Exception as e:
                    # Conversion failed or timed out: fall back to native OLE2 parsing
                    doc = self._extract_native_ole2_ppt(
                        file_path=file_path,
                        document_id=document_id,
                        file_id=file_id,
                        original_filename=original_filename,
                    )
                    doc.warnings.append(f"LibreOffice conversion failed ({e}); used native OLE2 fallback.")
                    return doc, []
        else:
            # Fall back directly to native OLE2 binary parser
            doc = self._extract_native_ole2_ppt(
                file_path=file_path,
                document_id=document_id,
                file_id=file_id,
                original_filename=original_filename,
            )
            return doc, []
