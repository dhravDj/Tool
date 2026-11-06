"""Canonical schemas for Universal File Converter and Content Extraction."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExtractionMode(StrEnum):
    """User-facing extraction modes."""

    PLAIN_TEXT = "plain_text"  # Mode A: Extract readable text only (.txt)
    STRUCTURED_TEXT = "structured_text"  # Mode B: Preserve hierarchy, tables, code blocks (.md)
    COMPLETE = "complete"  # Mode C: Full bundle (ZIP containing .txt, .md, .json, .csv, manifest)


class TargetFormat(StrEnum):
    """Supported output formats."""

    TXT = "txt"
    MD = "md"
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    ZIP = "zip"
    SRT = "srt"
    VTT = "vtt"


class ConversionStatus(StrEnum):
    """Lifecycle state of a conversion job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UniversalTable(BaseModel):
    """Tabular data representation with headers and row values."""

    title: str = ""
    sheet_name: str = ""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    col_count: int = 0


class UniversalCodeBlock(BaseModel):
    """Extracted code snippet or script block."""

    language: str = ""
    code: str = ""
    caption: str = ""
    line_count: int = 0


class UniversalTranscriptSegment(BaseModel):
    """Audio or video speech segment with timestamps."""

    start_seconds: float = 0.0
    end_seconds: float = 0.0
    speaker: str = ""
    text: str = ""
    confidence: float = 1.0


class UniversalSection(BaseModel):
    """Document section or slide with heading and body."""

    title: str
    level: int = 1
    content: str = ""
    page_or_slide_number: int | None = None


class UniversalContent(BaseModel):
    """Standardized representation of extracted content across all formats."""

    source_filename: str
    source_format: str
    title: str = ""
    author: str = ""
    page_count: int = 1
    word_count: int = 0
    paragraphs: list[str] = Field(default_factory=list)
    sections: list[UniversalSection] = Field(default_factory=list)
    tables: list[UniversalTable] = Field(default_factory=list)
    code_blocks: list[UniversalCodeBlock] = Field(default_factory=list)
    transcript_segments: list[UniversalTranscriptSegment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ConversionOptions(BaseModel):
    """Fine-grained configuration options for conversion."""

    ocr_enabled: bool = True
    ocr_language: str = "eng"
    preserve_tables: bool = True
    preserve_headings: bool = True
    preserve_page_numbers: bool = True
    include_metadata: bool = True
    sheet_name: str | None = None
    delimiter: str = ","


class ConversionRequest(BaseModel):
    """Request payload to convert an uploaded or stored file."""

    target_format: str = "txt"
    extraction_mode: str = "structured_text"
    options: ConversionOptions = Field(default_factory=ConversionOptions)


class ConversionResponse(BaseModel):
    """Response payload detailing conversion status, preview, and download info."""

    id: str
    status: str
    original_filename: str
    source_format: str
    target_format: str
    extraction_mode: str
    progress_percent: float = 0.0
    output_filename: str = ""
    output_size_bytes: int = 0
    mime_type: str = "text/plain"
    preview_content: str = ""
    download_url: str = ""
    duration_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None


class FormatCapabilities(BaseModel):
    """Capability matrix for input formats and their allowed output conversions."""

    input_format: str
    category: str
    display_name: str
    description: str
    supported_modes: list[str]
    allowed_output_formats: list[str]
    supports_ocr: bool = False
