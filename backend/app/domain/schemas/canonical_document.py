"""Canonical Document Schema for DocuMind AI.

Every supported document format (PDF, DOCX, DOC, TXT, MD, RTF, ODT, EPUB) is
normalized into this canonical representation, guaranteeing uniform consumption
by downstream storage, export, and search modules.
"""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from app.domain.enums import BlockType, ExtractionStatus

if TYPE_CHECKING:
    from app.plugins.interfaces.extractor import ExtractionResult


class CanonicalBlock(BaseModel):
    """Discrete semantic block within a document page."""

    block_id: str = Field(..., description="Unique deterministic or random block identifier")
    block_type: BlockType = Field(default=BlockType.PARAGRAPH, description="Semantic classification")
    text: str = Field(default="", description="Original extracted raw text without synthetic modifications")
    reading_order: int = Field(default=0, description="0-indexed natural reading order position")
    page_number: int = Field(default=1, description="1-indexed source document page number")
    bounding_box: list[float] | None = Field(
        default=None,
        description="Coordinates [x0, y0, x1, y1] in page points where available",
    )
    confidence: float | None = Field(default=None, description="Extraction or OCR confidence score (0.0 to 1.0)")
    extraction_engine: str = Field(default="native", description="Engine producing this block")
    provenance: str = Field(default="native", description="Source: native | ocr | layout_heuristic")
    warnings: list[str] = Field(default_factory=list, description="Parser or block-level warnings")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Block-specific attributes (e.g. heading_level, table_grid, language, image_ref)",
    )


class CanonicalPage(BaseModel):
    """Structural page representation with dimensions and contained blocks."""

    page_number: int = Field(..., description="1-indexed page sequence number")
    width: float | None = Field(default=None, description="Page width in points (72 dpi)")
    height: float | None = Field(default=None, description="Page height in points (72 dpi)")
    rotation: int = Field(default=0, description="Clockwise rotation in degrees (0, 90, 180, 270)")
    is_scanned: bool = Field(default=False, description="True if native digital text density is below threshold")
    ocr_applied: bool = Field(default=False, description="True if OCR was executed for this page")
    blocks: list[CanonicalBlock] = Field(default_factory=list, description="Blocks belonging to this page")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Page-specific attributes")


class CanonicalDocument(BaseModel):
    """Unified canonical representation of an extracted document."""

    document_id: str = Field(..., description="Unique document / file identifier")
    original_filename: str = Field(..., description="Original source filename")
    detected_format: str = Field(..., description="Canonical format ID (pdf, docx, rtf, etc.)")
    extraction_status: ExtractionStatus = Field(
        default=ExtractionStatus.COMPLETED,
        description="Status of the extraction process",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document-level metadata (author, title, date, etc.)",
    )
    page_count: int = Field(default=1, description="Total document pages")
    extraction_engine: str = Field(..., description="Primary extraction engine identifier")
    extraction_version: str = Field(default="1.0.0", description="Extraction engine version")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of extraction")
    pages: list[CanonicalPage] = Field(default_factory=list, description="Document pages")
    blocks: list[CanonicalBlock] = Field(
        default_factory=list,
        description="Flattened sequence of all blocks across all pages in reading order",
    )
    warnings: list[str] = Field(default_factory=list, description="Extraction warnings")
    errors: list[str] = Field(default_factory=list, description="Extraction errors")

    def to_extraction_result(self, execution_time_seconds: float = 0.0) -> "ExtractionResult":
        """Convert canonical document to the plugin interface ExtractionResult."""
        from app.plugins.interfaces.extractor import ExtractedElement, ExtractionResult

        elements: list[ExtractedElement] = []
        for block in self.blocks:
            elements.append(
                ExtractedElement(
                    element_type=block.block_type.value,
                    content=block.text,
                    page_number=block.page_number,
                    bounding_box=block.bounding_box,
                    confidence=block.confidence,
                    metadata={
                        **block.metadata,
                        "block_id": block.block_id,
                        "reading_order": block.reading_order,
                        "provenance": block.provenance,
                    },
                )
            )

        raw_text = "\n\n".join(b.text for b in self.blocks if b.text)

        return ExtractionResult(
            engine_name=self.extraction_engine,
            elements=elements,
            raw_text=raw_text,
            page_count=self.page_count,
            metadata={
                **self.metadata,
                "document_id": self.document_id,
                "detected_format": self.detected_format,
                "extraction_status": self.extraction_status.value,
                "warnings": self.warnings,
                "errors": self.errors,
            },
            execution_time_seconds=execution_time_seconds,
        )


class ExtractionManifest(BaseModel):
    """Operational manifest cataloging generated artifacts, performance, and diagnostics."""

    document_id: str = Field(...)
    original_filename: str = Field(...)
    detected_format: str = Field(...)
    extraction_engine: str = Field(...)
    extraction_version: str = Field(...)
    processing_timestamp: str = Field(...)
    execution_time_seconds: float = Field(...)
    page_count: int = Field(...)
    extracted_block_count: int = Field(...)
    scanned_page_count: int = Field(default=0)
    ocr_page_count: int = Field(default=0)
    ocr_engine: str | None = Field(default=None)
    overall_confidence: float = Field(default=1.0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    output_files: dict[str, str] = Field(
        default_factory=dict,
        description="Relative or URI paths to generated outputs (json, markdown, manifest, etc.)",
    )
    assets: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted embedded image or attachment metadata",
    )


class ExtractionRequest(BaseModel):
    """Payload for triggering a document extraction run."""

    password: str | None = Field(default=None, description="Optional password for encrypted documents (PDF)")
    extract_images: bool = Field(default=False, description="Extract and save embedded image assets")
    options: dict[str, Any] = Field(default_factory=dict, description="Additional extractor-specific options")


class ExtractionStatusResponse(BaseModel):
    """Summary of extraction status and generated artifacts."""

    file_id: str
    status: str
    engine: str
    detected_format: str
    page_count: int
    block_count: int
    scanned_pages: int
    ocr_applied_pages: int
    warnings: list[str]
    errors: list[str]
    output_files: dict[str, str]
    created_at: str


class ExtractionCapabilitiesResponse(BaseModel):
    """System-level document extraction and OCR capabilities."""

    supported_formats: list[str]
    engines: list[str]
    ocr_enabled: bool
    ocr_engine: str | None
    ocr_available: bool
