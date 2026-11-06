"""Universal Content Normalization Schemas for DocuMind AI (Phase 11).

Defines KnowledgeDocument, ContentBlock, KnowledgeChunk, and SourceReference models
that normalize extracted data across all file types (Phases 1-10).
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Exact source provenance and locator information within a file."""

    source_file_id: str = Field(..., description="UUID of source FileRecord")
    original_filename: str = Field(..., description="Basename of source file")
    source_type: str = Field(
        ...,
        description="document, image, spreadsheet, presentation, audio, video, code, structured_data, archive",
    )
    formatted_citation: str = Field(
        ...,
        description="Human-readable citation string (e.g. 'doc.pdf — Page 12')",
    )
    page_number: int | None = Field(default=None, description="1-indexed document page number")
    paragraph_index: int | None = Field(default=None, description="Paragraph index")
    sheet_name: str | None = Field(default=None, description="Spreadsheet sheet name")
    cell_range: str | None = Field(default=None, description="Spreadsheet cell coordinate range (e.g. 'B2:F12')")
    slide_number: int | None = Field(default=None, description="1-indexed presentation slide number")
    element_id: str | None = Field(default=None, description="Shape, diagram, or chart element ID")
    bounding_box: list[float] | None = Field(
        default=None,
        description="Image bounding box [ymin, xmin, ymax, xmax]",
    )
    timestamp_start: float | None = Field(default=None, description="Audio/video start time in seconds")
    timestamp_end: float | None = Field(default=None, description="Audio/video end time in seconds")
    scene_id: str | None = Field(default=None, description="Video scene boundary ID")
    line_start: int | None = Field(default=None, description="Source code starting line")
    line_end: int | None = Field(default=None, description="Source code ending line")
    json_path: str | None = Field(default=None, description="Structured data JSONPath (e.g. '$.users[0].name')")
    archive_path: str | None = Field(default=None, description="Relative archive entry path")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional provenance context")


class ContentBlock(BaseModel):
    """Discrete semantic block of extracted content with exact provenance."""

    block_id: str = Field(..., description="Unique deterministic block identifier")
    content: str = Field(..., description="Extracted textual or structured content")
    block_type: str = Field(
        default="paragraph",
        description="paragraph, heading, table, code, transcript_segment, slide, structured_record, image_caption, archive_manifest",
    )
    source_reference: SourceReference = Field(..., description="Exact provenance locator")
    token_estimate: int = Field(default=0, description="Estimated token count")
    extraction_confidence: float | None = Field(default=None, description="Extraction or OCR confidence score (0.0 to 1.0)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Block-specific metadata attributes")


class KnowledgeDocument(BaseModel):
    """Universal normalized document representation across all file modalities."""

    knowledge_document_id: str = Field(..., description="Unique knowledge document ID")
    source_file_id: str = Field(..., description="Source file UUID")
    parent_archive_id: str | None = Field(default=None, description="Parent archive file UUID if unpacked")
    source_type: str = Field(
        ...,
        description="document, image, spreadsheet, presentation, audio, video, code, structured_data, archive",
    )
    content_type: str = Field(..., description="MIME type or format identifier")
    title: str = Field(..., description="Document title or original filename")
    content_blocks: list[ContentBlock] = Field(default_factory=list, description="Ordered sequence of semantic content blocks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document-level metadata")
    source_references: list[SourceReference] = Field(default_factory=list, description="Collection of unique source references")
    extraction_status: str = Field(default="completed", description="Extraction status")
    language: str = Field(default="en", description="Primary detected language")
    content_hash: str = Field(..., description="SHA256 checksum of document content")
    processing_version: str = Field(default="1.0.0", description="DocuMind AI engine version")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 creation timestamp",
    )


class KnowledgeChunk(BaseModel):
    """Indexed fragment of a KnowledgeDocument for semantic search and RAG retrieval."""

    chunk_id: str = Field(..., description="Unique deterministic chunk ID: chunk_{doc_id}_{index}")
    knowledge_document_id: str = Field(..., description="Parent KnowledgeDocument ID")
    source_file_id: str = Field(..., description="Parent FileRecord UUID")
    chunk_index: int = Field(..., description="0-indexed position within document")
    content: str = Field(..., description="Text content formatted for embedding and LLM prompt context")
    token_count: int = Field(default=0, description="Token count")
    source_reference: SourceReference = Field(..., description="Source reference for exact citation grounding")
    embedding_status: str = Field(default="pending", description="pending, embedded, failed")
    content_hash: str = Field(..., description="SHA256 hash of chunk content for cache & deduplication")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk attributes (block_type, headings, etc.)")
