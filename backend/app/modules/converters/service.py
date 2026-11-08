"""Universal Conversion Service orchestrating extraction, normalization, and export."""

import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import ConversionRecord
from app.modules.archive_intelligence.pipeline import ArchiveIntelligencePipeline
from app.modules.audio_intelligence.pipeline import AudioIntelligencePipeline
from app.modules.code_intelligence.pipeline import CodeIntelligencePipeline
from app.modules.converters.adapters import (
    ArchiveAdapter,
    AudioAdapter,
    CodeAdapter,
    DocumentAdapter,
    ImageAdapter,
    PresentationAdapter,
    SpreadsheetAdapter,
    StructuredDataAdapter,
    VideoAdapter,
)
from app.modules.converters.schemas import (
    ConversionOptions,
    ConversionStatus,
    ExtractionMode,
    FormatCapabilities,
    TargetFormat,
    UniversalContent,
)
from app.modules.converters.writers import (
    BundleWriter,
    CsvWriter,
    HtmlWriter,
    JsonWriter,
    MarkdownWriter,
    SubtitleWriter,
    TxtWriter,
)
from app.modules.extraction.pipeline import ExtractionPipeline
from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.formats.categories import FormatCategory
from app.modules.image_intelligence.pipeline import ImageIntelligencePipeline
from app.modules.presentation_intelligence.pipeline import PresentationIntelligencePipeline
from app.modules.spreadsheet_intelligence.pipeline import SpreadsheetIntelligencePipeline
from app.modules.structured_data_intelligence.pipeline import StructuredDataIntelligencePipeline
from app.modules.video_intelligence.pipeline import VideoIntelligencePipeline

logger = logging.getLogger(__name__)

# Capability mappings
FORMAT_CAPABILITIES: dict[str, dict[str, Any]] = {
    # Documents
    "pdf": {
        "category": "document",
        "display_name": "Portable Document Format",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "docx": {
        "category": "document",
        "display_name": "Microsoft Word OpenXML",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "doc": {
        "category": "document",
        "display_name": "Legacy Microsoft Word",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "odt": {
        "category": "document",
        "display_name": "OpenDocument Text",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "rtf": {
        "category": "document",
        "display_name": "Rich Text Format",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "txt": {
        "category": "document",
        "display_name": "Plain Text Document",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "md": {
        "category": "document",
        "display_name": "Markdown Document",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "epub": {
        "category": "document",
        "display_name": "Electronic Publication eBook",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Spreadsheets
    "xlsx": {
        "category": "spreadsheet",
        "display_name": "Microsoft Excel OpenXML",
        "allowed_outputs": ["csv", "txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "xls": {
        "category": "spreadsheet",
        "display_name": "Legacy Microsoft Excel",
        "allowed_outputs": ["csv", "txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "csv": {
        "category": "spreadsheet",
        "display_name": "Comma Separated Values",
        "allowed_outputs": ["csv", "txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "tsv": {
        "category": "spreadsheet",
        "display_name": "Tab Separated Values",
        "allowed_outputs": ["csv", "txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "ods": {
        "category": "spreadsheet",
        "display_name": "OpenDocument Spreadsheet",
        "allowed_outputs": ["csv", "txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Presentations
    "pptx": {
        "category": "presentation",
        "display_name": "Microsoft PowerPoint OpenXML",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "ppt": {
        "category": "presentation",
        "display_name": "Legacy Microsoft PowerPoint",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "odp": {
        "category": "presentation",
        "display_name": "OpenDocument Presentation",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Images
    "png": {
        "category": "image",
        "display_name": "Portable Network Graphics",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "jpg": {
        "category": "image",
        "display_name": "JPEG Image",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "jpeg": {
        "category": "image",
        "display_name": "JPEG Image",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "webp": {
        "category": "image",
        "display_name": "WebP Image",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "tiff": {
        "category": "image",
        "display_name": "Tag Image File Format",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "bmp": {
        "category": "image",
        "display_name": "Bitmap Image",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "svg": {
        "category": "image",
        "display_name": "Scalable Vector Graphics",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Audio
    "mp3": {
        "category": "audio",
        "display_name": "MPEG-1 Audio Layer III",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "wav": {
        "category": "audio",
        "display_name": "Waveform Audio File Format",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "m4a": {
        "category": "audio",
        "display_name": "MPEG-4 Audio",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "aac": {
        "category": "audio",
        "display_name": "Advanced Audio Coding",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "flac": {
        "category": "audio",
        "display_name": "Free Lossless Audio Codec",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "ogg": {
        "category": "audio",
        "display_name": "Ogg Vorbis Audio",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Video
    "mp4": {
        "category": "video",
        "display_name": "MPEG-4 Part 14 Video",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "mkv": {
        "category": "video",
        "display_name": "Matroska Video",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "mov": {
        "category": "video",
        "display_name": "Apple QuickTime Movie",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "avi": {
        "category": "video",
        "display_name": "Audio Video Interleave",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": True,
    },
    "webm": {
        "category": "video",
        "display_name": "WebM Video",
        "allowed_outputs": ["txt", "md", "srt", "vtt", "json", "html", "zip"],
        "supports_ocr": True,
    },
    # Code
    "py": {
        "category": "code",
        "display_name": "Python Script",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "js": {
        "category": "code",
        "display_name": "JavaScript Source",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "ts": {
        "category": "code",
        "display_name": "TypeScript Source",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "jsx": {
        "category": "code",
        "display_name": "React JSX Source",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "tsx": {
        "category": "code",
        "display_name": "React TSX Source",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "html": {
        "category": "code",
        "display_name": "HTML Document / Source",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "css": {
        "category": "code",
        "display_name": "Cascading Style Sheets",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "java": {
        "category": "code",
        "display_name": "Java Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "c": {
        "category": "code",
        "display_name": "C Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "cpp": {
        "category": "code",
        "display_name": "C++ Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "go": {
        "category": "code",
        "display_name": "Go Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "rs": {
        "category": "code",
        "display_name": "Rust Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "php": {
        "category": "code",
        "display_name": "PHP Source Code",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    "sql": {
        "category": "code",
        "display_name": "SQL Query / Schema Script",
        "allowed_outputs": ["txt", "md", "json", "html", "zip"],
        "supports_ocr": False,
    },
    # Structured Data
    "json": {
        "category": "structured_data",
        "display_name": "JavaScript Object Notation",
        "allowed_outputs": ["json", "txt", "md", "csv", "html", "zip"],
        "supports_ocr": False,
    },
    "xml": {
        "category": "structured_data",
        "display_name": "Extensible Markup Language",
        "allowed_outputs": ["xml", "json", "txt", "md", "csv", "html", "zip"],
        "supports_ocr": False,
    },
    "yaml": {
        "category": "structured_data",
        "display_name": "YAML Ain't Markup Language",
        "allowed_outputs": ["json", "txt", "md", "html", "zip"],
        "supports_ocr": False,
    },
    "toml": {
        "category": "structured_data",
        "display_name": "Tom's Obvious Minimal Language",
        "allowed_outputs": ["json", "txt", "md", "html", "zip"],
        "supports_ocr": False,
    },
    "parquet": {
        "category": "structured_data",
        "display_name": "Apache Parquet Columnar Data",
        "allowed_outputs": ["csv", "json", "txt", "md", "html", "zip"],
        "supports_ocr": False,
    },
    # Archives
    "zip": {
        "category": "archive",
        "display_name": "ZIP Archive Container",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "7z": {
        "category": "archive",
        "display_name": "7-Zip Compressed Archive",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "tar": {
        "category": "archive",
        "display_name": "Tape Archive Container",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "tar.gz": {
        "category": "archive",
        "display_name": "Gzip Compressed TAR Archive",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "tar.bz2": {
        "category": "archive",
        "display_name": "Bzip2 Compressed TAR Archive",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "tar.xz": {
        "category": "archive",
        "display_name": "XZ Compressed TAR Archive",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
    "gz": {
        "category": "archive",
        "display_name": "Gzip Compressed File",
        "allowed_outputs": ["zip", "txt", "md", "json", "html"],
        "supports_ocr": False,
    },
}


class UniversalConversionService:
    """Production conversion orchestrator coordinating extraction, normalization, and export."""

    def __init__(self) -> None:
        self.detector = UniversalFileDetector()
        self.doc_pipeline = ExtractionPipeline()
        self.spreadsheet_pipeline = SpreadsheetIntelligencePipeline()
        self.presentation_pipeline = PresentationIntelligencePipeline()
        self.image_pipeline = ImageIntelligencePipeline()
        self.audio_pipeline = AudioIntelligencePipeline()
        self.video_pipeline = VideoIntelligencePipeline()
        self.code_pipeline = CodeIntelligencePipeline()
        self.structured_pipeline = StructuredDataIntelligencePipeline()
        self.archive_pipeline = ArchiveIntelligencePipeline()

    def get_supported_capabilities(self) -> list[FormatCapabilities]:
        """Return full capability matrix of supported inputs and target formats."""
        items: list[FormatCapabilities] = []
        for fmt, meta in FORMAT_CAPABILITIES.items():
            items.append(
                FormatCapabilities(
                    input_format=fmt,
                    category=meta["category"],
                    display_name=meta["display_name"],
                    description=f"{meta['display_name']} extraction and universal conversion.",
                    supported_modes=[
                        ExtractionMode.PLAIN_TEXT.value,
                        ExtractionMode.STRUCTURED_TEXT.value,
                        ExtractionMode.COMPLETE.value,
                    ],
                    allowed_output_formats=meta["allowed_outputs"],
                    supports_ocr=meta["supports_ocr"],
                )
            )
        return items

    async def convert_file(
        self,
        file_path: Path,
        target_format: str,
        extraction_mode: str = "structured_text",
        original_filename: str = "",
        options: ConversionOptions | dict[str, Any] | None = None,
        session: AsyncSession | None = None,
        owner_id: uuid.UUID | None = None,
        source_file_id: uuid.UUID | None = None,
    ) -> ConversionRecord:
        """Execute end-to-end extraction and conversion on a file."""
        t_start = time.perf_counter()
        effective_filename = original_filename or file_path.name
        opts_dict = options.model_dump() if isinstance(options, ConversionOptions) else (options or {})

        # 1. Automatic format detection
        detection = self.detector.detect_file(file_path, effective_filename)
        detected_fmt = detection.format_id.lower().strip()
        # Fallback to extension if format_id is generic
        if detected_fmt in ("unknown", "generic_binary", "text") or not detected_fmt:
            ext = file_path.suffix.lstrip(".").lower()
            if ext in FORMAT_CAPABILITIES:
                detected_fmt = ext
            else:
                detected_fmt = detection.extension or "txt"

        category = detection.category.value if hasattr(detection.category, "value") else str(detection.category)

        # Mode normalization
        if extraction_mode == ExtractionMode.COMPLETE.value:
            effective_target_fmt = TargetFormat.ZIP.value
        elif extraction_mode == ExtractionMode.PLAIN_TEXT.value and target_format == "default":
            effective_target_fmt = TargetFormat.TXT.value
        elif extraction_mode == ExtractionMode.STRUCTURED_TEXT.value and target_format == "default":
            effective_target_fmt = TargetFormat.MD.value
        else:
            effective_target_fmt = target_format.lower().strip()

        # Create record in pending status
        conversion_id = uuid.uuid4()
        record = ConversionRecord(
            id=conversion_id,
            owner_id=owner_id,
            source_file_id=source_file_id,
            original_filename=effective_filename,
            source_format=detected_fmt,
            target_format=effective_target_fmt,
            extraction_mode=extraction_mode,
            status=ConversionStatus.PROCESSING.value,
            progress_percent=20.0,
            options=opts_dict,
            warnings=list(detection.warnings),
        )

        if session:
            session.add(record)
            await session.commit()
            await session.refresh(record)

        try:
            # 2. Route extraction and adapt to UniversalContent
            content = await self._extract_universal_content(
                file_path=file_path,
                format_id=detected_fmt,
                category=category,
                original_filename=effective_filename,
                options=opts_dict,
            )

            # 3. Export to requested output format
            base_stem = Path(effective_filename).stem or "converted"
            storage_dir = Path(getattr(settings, "STORAGE_LOCAL_ROOT", "./storage")) / "conversions" / str(conversion_id)
            storage_dir.mkdir(parents=True, exist_ok=True)

            out_filename, out_path, mime_type, preview_text = self._write_output(
                content=content,
                target_format=effective_target_fmt,
                base_stem=base_stem,
                storage_dir=storage_dir,
            )

            duration = time.perf_counter() - t_start
            file_size = out_path.stat().st_size if out_path.exists() else len(preview_text.encode("utf-8"))

            record.status = ConversionStatus.COMPLETED.value
            record.progress_percent = 100.0
            record.output_filename = out_filename
            record.output_path = str(out_path)
            record.output_size_bytes = file_size
            record.mime_type = mime_type
            record.preview_content = preview_text[:50000]
            record.duration_seconds = round(duration, 3)
            record.completed_at = datetime.now(UTC)
            if content.warnings:
                record.warnings = list(set(record.warnings + content.warnings))

            if session:
                await session.commit()
                await session.refresh(record)

            logger.info(
                f"Conversion completed: {effective_filename} ({detected_fmt}) -> {out_filename} in {duration:.3f}s"
            )
            return record

        except Exception as exc:
            duration = time.perf_counter() - t_start
            logger.exception(f"Conversion failed for {effective_filename}: {exc}")
            record.status = ConversionStatus.FAILED.value
            record.progress_percent = 100.0
            record.error_message = str(exc)
            record.duration_seconds = round(duration, 3)
            record.completed_at = datetime.now(UTC)
            if session:
                await session.commit()
                await session.refresh(record)
            raise

    async def _extract_universal_content(
        self,
        file_path: Path,
        format_id: str,
        category: str,
        original_filename: str,
        options: dict[str, Any],
    ) -> UniversalContent:
        """Route to format-specific engine and normalize into UniversalContent."""
        fmt = format_id.lower()

        # A. Spreadsheets
        if fmt in ("xlsx", "xls", "csv", "tsv", "ods") or category == FormatCategory.SPREADSHEET.value:
            sheet_doc = self.spreadsheet_pipeline.extract_document(
                file_path=file_path,
                format_id=fmt,
                original_filename=original_filename,
                options=options,
            )
            return SpreadsheetAdapter.adapt(sheet_doc)

        # B. Presentations
        if fmt in ("pptx", "ppt", "odp") or category == FormatCategory.PRESENTATION.value:
            pres_doc, _ = await self.presentation_pipeline.extract_document(
                file_path=file_path,
                format_id=fmt,
                original_filename=original_filename,
                options=options,
            )
            return PresentationAdapter.adapt(pres_doc, original_filename)

        # C. Code
        if fmt in (
            "py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"
        ) or category == FormatCategory.CODE.value:
            code_doc = await self.code_pipeline.analyze_code(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
                language=fmt,
                options=options,
            )
            return CodeAdapter.adapt(code_doc, original_filename)

        # D. Structured Data
        if fmt in ("json", "xml", "yaml", "yml", "toml", "parquet") or category == FormatCategory.STRUCTURED_DATA.value:
            struct_doc = await self.structured_pipeline.analyze_structured_data(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
                format_id=fmt,
                options=options,
            )
            return StructuredDataAdapter.adapt(struct_doc, original_filename)

        # E. Archives
        if fmt in ("zip", "7z", "tar", "gz", "bz2", "xz", "tgz", "tbz2", "txz") or category == FormatCategory.ARCHIVE.value:
            archive_doc = await self.archive_pipeline.analyze_archive(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
            )
            return ArchiveAdapter.adapt(archive_doc, original_filename)

        # F. Images
        if fmt in ("png", "jpg", "jpeg", "webp", "tiff", "bmp", "svg") or category == FormatCategory.IMAGE.value:
            image_doc, _ = self.image_pipeline.process_image_path(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                filename=original_filename,
                format_id=fmt,
                options=options,
            )
            return ImageAdapter.adapt(image_doc, original_filename)

        # G. Audio
        if fmt in ("mp3", "wav", "m4a", "aac", "flac", "ogg") or category == FormatCategory.AUDIO.value:
            audio_doc, _ = await self.audio_pipeline.analyze_audio(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
                format_id=fmt,
                options=options,
            )
            return AudioAdapter.adapt(audio_doc, original_filename)

        # H. Video
        if fmt in ("mp4", "mkv", "mov", "avi", "webm") or category == FormatCategory.VIDEO.value:
            video_doc, _ = await self.video_pipeline.analyze_video(
                file_path=file_path,
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
                format_id=fmt,
                options=options,
            )
            return VideoAdapter.adapt(video_doc, original_filename)

        # I. Documents (PDF, DOCX, DOC, ODT, RTF, TXT, MD, EPUB) and default fallback
        canonical_doc = await self.doc_pipeline.extract_path(
            file_path=file_path,
            format_id=fmt if fmt in self.doc_pipeline.list_supported_formats() else "txt",
            original_filename=original_filename,
            options=options,
        )
        return DocumentAdapter.adapt(canonical_doc)

    def _write_output(
        self,
        content: UniversalContent,
        target_format: str,
        base_stem: str,
        storage_dir: Path,
    ) -> tuple[str, Path, str, str]:
        """Convert UniversalContent into target format, write to disk, and return metadata."""
        tgt = target_format.lower().strip()

        # 1. Mode C Complete Bundle (ZIP)
        if tgt == TargetFormat.ZIP.value:
            out_filename = f"{base_stem}_extracted.zip"
            out_path = storage_dir / out_filename
            BundleWriter.write_zip(content, out_path)
            preview = f"Complete extraction bundle created: {out_filename}\nContains TXT, Markdown, JSON, HTML, and extracted CSV tables."
            return out_filename, out_path, "application/zip", preview

        # 2. CSV Table Export
        if tgt == TargetFormat.CSV.value:
            out_filename = f"{base_stem}.csv"
            out_path = storage_dir / out_filename
            csv_str = CsvWriter.write(content)
            out_path.write_text(csv_str, encoding="utf-8")
            return out_filename, out_path, "text/csv", csv_str

        # 3. Markdown Export
        if tgt == TargetFormat.MD.value:
            out_filename = f"{base_stem}.md"
            out_path = storage_dir / out_filename
            md_str = MarkdownWriter.write(content)
            out_path.write_text(md_str, encoding="utf-8")
            return out_filename, out_path, "text/markdown", md_str

        # 4. JSON Export
        if tgt == TargetFormat.JSON.value:
            out_filename = f"{base_stem}.json"
            out_path = storage_dir / out_filename
            json_str = JsonWriter.write(content)
            out_path.write_text(json_str, encoding="utf-8")
            return out_filename, out_path, "application/json", json_str

        # 5. HTML Export
        if tgt == TargetFormat.HTML.value:
            out_filename = f"{base_stem}.html"
            out_path = storage_dir / out_filename
            html_str = HtmlWriter.write(content)
            out_path.write_text(html_str, encoding="utf-8")
            return out_filename, out_path, "text/html", html_str

        # 6. Subtitles (SRT / VTT)
        if tgt == TargetFormat.SRT.value:
            out_filename = f"{base_stem}.srt"
            out_path = storage_dir / out_filename
            srt_str = SubtitleWriter.write_srt(content)
            out_path.write_text(srt_str, encoding="utf-8")
            return out_filename, out_path, "application/x-subrip", srt_str

        if tgt == TargetFormat.VTT.value:
            out_filename = f"{base_stem}.vtt"
            out_path = storage_dir / out_filename
            vtt_str = SubtitleWriter.write_vtt(content)
            out_path.write_text(vtt_str, encoding="utf-8")
            return out_filename, out_path, "text/vtt", vtt_str

        # 7. Default: Plain Text (.txt) (Mode A)
        out_filename = f"{base_stem}.txt"
        out_path = storage_dir / out_filename
        txt_str = TxtWriter.write(content)
        out_path.write_text(txt_str, encoding="utf-8")
        return out_filename, out_path, "text/plain", txt_str
