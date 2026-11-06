"""Document Extraction Pipeline Orchestrator."""

import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.enums import ExtractionStatus, FileStatus
from app.domain.schemas.canonical_document import (
    CanonicalDocument,
    ExtractionManifest,
)
from app.infrastructure.database.models import ExtractionRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.extraction.adapters.base import (
    BaseDocumentExtractor,
    CorruptedDocumentError,
    ExtractionError,
    PageLimitExceededError,
    PasswordRequiredError,
    UnsupportedFormatError,
)
from app.modules.extraction.adapters.doc import LegacyDocExtractor
from app.modules.extraction.adapters.docx import DocxExtractor
from app.modules.extraction.adapters.epub import EPUBExtractor
from app.modules.extraction.adapters.markdown import MarkdownExtractor
from app.modules.extraction.adapters.odt import ODTExtractor
from app.modules.extraction.adapters.pdf import PDFExtractor
from app.modules.extraction.adapters.rtf import RTFExtractor
from app.modules.extraction.adapters.text import PlainTextExtractor
from app.modules.extraction.generators.json_generator import JSONGenerator
from app.modules.extraction.generators.manifest_generator import ManifestGenerator
from app.modules.extraction.generators.markdown_generator import MarkdownGenerator
from app.modules.files.detection.detector import UniversalFileDetector

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Orchestrates document content extraction across all supported formats."""

    def __init__(self) -> None:
        self._extractors: dict[str, BaseDocumentExtractor] = {}
        self._register_default_extractors()

    def register_extractor(self, extractor: BaseDocumentExtractor) -> None:
        """Register an extractor instance for its supported formats."""
        for fmt in extractor.supported_formats:
            self._extractors[fmt.lower()] = extractor

    def get_extractor(self, format_id: str) -> BaseDocumentExtractor | None:
        """Lookup an extractor by canonical format ID."""
        return self._extractors.get(format_id.lower())

    def list_supported_formats(self) -> list[str]:
        """Return list of format IDs that currently have an active extractor."""
        return sorted(self._extractors.keys())

    def _register_default_extractors(self) -> None:
        """Initialize and index standard Phase 3 format adapters."""
        pdf_extractor = PDFExtractor()
        docx_extractor = DocxExtractor()
        doc_extractor = LegacyDocExtractor()
        text_extractor = PlainTextExtractor()
        md_extractor = MarkdownExtractor()
        rtf_extractor = RTFExtractor()
        odt_extractor = ODTExtractor()
        epub_extractor = EPUBExtractor()

        for extractor in [
            pdf_extractor,
            docx_extractor,
            doc_extractor,
            text_extractor,
            md_extractor,
            rtf_extractor,
            odt_extractor,
            epub_extractor,
        ]:
            self.register_extractor(extractor)

    async def extract_path(
        self,
        file_path: Path,
        format_id: str,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Run extraction on a filesystem path without database dependencies."""
        extractor = self.get_extractor(format_id)
        if not extractor:
            raise UnsupportedFormatError(
                f"No extraction engine registered for format '{format_id}'. "
                f"Supported formats: {self.list_supported_formats()}"
            )

        opts = options or {}
        return await extractor.extract_document(
            file_path=file_path,
            original_filename=original_filename or file_path.name,
            options=opts,
        )

    async def extract_file_record(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> tuple[CanonicalDocument, ExtractionManifest]:
        """Orchestrate end-to-end extraction for an ingested database FileRecord."""
        start_time = time.monotonic()
        opts = dict(options or {})

        # 1. Fetch File Record
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        result = await session.execute(stmt)
        file_record = result.scalar_one_or_none()
        if not file_record:
            raise ExtractionError(f"File record with ID '{file_id}' not found.")

        # 2. Resolve Local File Path
        local_path = local_storage.get_local_path(file_record.storage_path)
        if not local_path or not local_path.exists():
            raise ExtractionError(
                f"Physical file missing at storage path '{file_record.storage_path}'"
            )

        # 3. Ensure Detection Has Run
        if not file_record.detection_format_id:
            detector = UniversalFileDetector()
            detection_res = detector.detect_file(
                local_path,
                original_filename=file_record.original_filename,
            )
            file_record.detection_format_id = detection_res.format_id
            file_record.claimed_extension = detection_res.claimed_extension
            file_record.actual_extension = detection_res.extension
            file_record.format_category = (
                detection_res.category.value if detection_res.category else None
            )
            file_record.confidence_score = detection_res.confidence_score
            file_record.confidence_level = detection_res.confidence_level.value
            file_record.support_status = detection_res.support_status.value
            file_record.is_valid = detection_res.is_valid
            file_record.is_mismatch = detection_res.is_mismatch
            file_record.is_corrupted = detection_res.is_corrupted
            file_record.is_suspicious = detection_res.is_suspicious
            file_record.detection_evidence = {"items": [e.details for e in detection_res.evidence]}
            file_record.detection_warnings = detection_res.warnings
            file_record.file_metadata = detection_res.metadata
            file_record.detected_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(file_record)

        format_id = (file_record.detection_format_id or file_record.extension).lower()
        extractor = self.get_extractor(format_id)

        if not extractor:
            raise UnsupportedFormatError(
                f"File format '{format_id}' is not supported for content extraction. "
                f"Supported formats: {self.list_supported_formats()}"
            )

        # 4. Prepare Output Directories
        base_dir = local_storage.get_local_path("processed")
        if base_dir is None:
            base_dir = Path(settings.STORAGE_LOCAL_ROOT) / "processed"
        processed_dir = base_dir / str(file_id)
        processed_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = processed_dir / "assets"

        opts.update(
            {
                "document_id": str(file_id),
                "assets_dir": str(assets_dir),
            }
        )

        # 5. Execute Extraction
        canonical_doc: CanonicalDocument
        try:
            canonical_doc = await asyncio.wait_for(
                extractor.extract_document(
                    file_path=local_path,
                    original_filename=file_record.original_filename,
                    options=opts,
                ),
                timeout=settings.EXTRACTION_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            canonical_doc = extractor._create_empty_document(
                document_id=str(file_id),
                original_filename=file_record.original_filename,
                detected_format=format_id,
                status=ExtractionStatus.FAILED,
                error=f"Extraction timed out after {settings.EXTRACTION_TIMEOUT_SECONDS}s",
            )
        except PasswordRequiredError as exc:
            canonical_doc = extractor._create_empty_document(
                document_id=str(file_id),
                original_filename=file_record.original_filename,
                detected_format=format_id,
                status=ExtractionStatus.PASSWORD_REQUIRED,
                error=str(exc),
            )
        except PageLimitExceededError as exc:
            canonical_doc = extractor._create_empty_document(
                document_id=str(file_id),
                original_filename=file_record.original_filename,
                detected_format=format_id,
                status=ExtractionStatus.FAILED,
                error=str(exc),
            )
        except CorruptedDocumentError as exc:
            canonical_doc = extractor._create_empty_document(
                document_id=str(file_id),
                original_filename=file_record.original_filename,
                detected_format=format_id,
                status=ExtractionStatus.FAILED,
                error=str(exc),
            )
        except Exception as exc:
            logger.exception(f"Unexpected extraction error on file {file_id}: {exc}")
            canonical_doc = extractor._create_empty_document(
                document_id=str(file_id),
                original_filename=file_record.original_filename,
                detected_format=format_id,
                status=ExtractionStatus.FAILED,
                error=f"Extraction failed: {exc}",
            )

        elapsed_time = time.monotonic() - start_time

        # 6. Generate and Save Outputs
        json_output = JSONGenerator.generate(canonical_doc)
        md_output = MarkdownGenerator.generate(canonical_doc)

        json_file = processed_dir / "canonical_document.json"
        md_file = processed_dir / "document.md"
        manifest_file = processed_dir / "manifest.json"

        json_file.write_text(json_output, encoding="utf-8")
        md_file.write_text(md_output, encoding="utf-8")

        output_files_map = {
            "canonical_json": f"processed/{file_id}/canonical_document.json",
            "markdown": f"processed/{file_id}/document.md",
            "manifest": f"processed/{file_id}/manifest.json",
        }

        # Collect any extracted assets
        assets_list: list[dict[str, Any]] = []
        if assets_dir.exists():
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    assets_list.append(
                        {
                            "name": asset_file.name,
                            "size": asset_file.stat().st_size,
                            "path": f"processed/{file_id}/assets/{asset_file.name}",
                        }
                    )

        manifest = ManifestGenerator.generate(
            document=canonical_doc,
            execution_time_seconds=elapsed_time,
            output_files=output_files_map,
            assets=assets_list,
            ocr_engine=settings.OCR_ENGINE if settings.OCR_ENABLED else None,
        )

        manifest_file.write_text(
            json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 7. Record to Database (ExtractionRecord & FileRecord)
        extraction_record = ExtractionRecord(
            file_id=file_id,
            engine=canonical_doc.extraction_engine,
            output_format="canonical_json",
            output_path=output_files_map["canonical_json"],
            record_metadata={
                "manifest": manifest.model_dump(),
                "extraction_status": canonical_doc.extraction_status.value,
                "page_count": canonical_doc.page_count,
                "block_count": len(canonical_doc.blocks),
                "execution_time_seconds": manifest.execution_time_seconds,
                "warnings": canonical_doc.warnings,
                "errors": canonical_doc.errors,
            },
        )
        session.add(extraction_record)

        if canonical_doc.extraction_status in (
            ExtractionStatus.COMPLETED,
            ExtractionStatus.COMPLETED_WITH_WARNINGS,
        ):
            file_record.status = FileStatus.PROCESSED.value
        else:
            file_record.status = FileStatus.ERROR.value

        await session.commit()
        await session.refresh(file_record)

        return canonical_doc, manifest


# Global Pipeline Instance
extraction_pipeline = ExtractionPipeline()
