"""Operational execution manifest generator for Presentation Intelligence."""

from app.modules.presentation_intelligence.schemas.presentation_document import (
    PresentationDocument,
    PresentationManifest,
)


class PresentationManifestGenerator:
    """Builds operational manifest recording pipeline runtime execution and exported artifacts."""

    @classmethod
    def generate(
        cls,
        doc: PresentationDocument,
        source_filename: str,
        source_format: str,
        processing_time_seconds: float,
        artifacts: dict[str, str],
        errors: list[str] | None = None,
    ) -> PresentationManifest:
        """Create a PresentationManifest summarizing document metrics and artifact locations."""
        total_elements = sum(len(s.elements) for s in doc.slides)

        return PresentationManifest(
            document_id=doc.document_id,
            file_id=doc.file_id,
            source_filename=source_filename,
            source_format=source_format,
            status=doc.processing_status,
            engine_name=doc.extraction_metadata.get("engine_name", "unknown"),
            engine_version=doc.extraction_metadata.get("engine_version", "1.0.0"),
            processing_time_seconds=round(processing_time_seconds, 3),
            slide_count=doc.slide_count,
            hidden_slide_count=doc.metadata.hidden_slide_count,
            total_elements=total_elements,
            asset_count=len(doc.assets),
            table_count=len(doc.tables),
            chart_count=len(doc.charts),
            diagram_count=len(doc.diagrams),
            artifacts=artifacts,
            warnings=doc.warnings,
            errors=errors or [],
        )
