"""Manifest output generator for document extraction runs."""

from datetime import UTC, datetime
from typing import Any

from app.domain.schemas.canonical_document import CanonicalDocument, ExtractionManifest


class ManifestGenerator:
    """Builds an ExtractionManifest summarizing performance, confidence, and output file maps."""

    @classmethod
    def generate(
        cls,
        document: CanonicalDocument,
        execution_time_seconds: float,
        output_files: dict[str, str],
        assets: list[dict[str, Any]] | None = None,
        ocr_engine: str | None = None,
    ) -> ExtractionManifest:
        scanned_pages = sum(1 for p in document.pages if p.is_scanned)
        ocr_pages = sum(1 for p in document.pages if p.ocr_applied)

        # Average confidence across blocks that carry a confidence score
        confs = [b.confidence for b in document.blocks if b.confidence is not None]
        overall_conf = (sum(confs) / len(confs)) if confs else 1.0

        return ExtractionManifest(
            document_id=document.document_id,
            original_filename=document.original_filename,
            detected_format=document.detected_format,
            extraction_engine=document.extraction_engine,
            extraction_version=document.extraction_version,
            processing_timestamp=datetime.now(UTC).isoformat(),
            execution_time_seconds=round(execution_time_seconds, 4),
            page_count=document.page_count,
            extracted_block_count=len(document.blocks),
            scanned_page_count=scanned_pages,
            ocr_page_count=ocr_pages,
            ocr_engine=ocr_engine,
            overall_confidence=round(overall_conf, 3),
            warnings=document.warnings,
            errors=document.errors,
            output_files=output_files,
            assets=assets or [],
        )
