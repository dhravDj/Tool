"""Canonical Pydantic v2 schemas for the Presentation Intelligence Engine.

Represents presentations, slide structures, text hierarchy, bullet nesting,
tables, native & inferred charts, diagrams, embedded assets, speaker notes,
and export manifests across PPTX, PPT, and ODP formats.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ElementType(str, Enum):
    """Semantic type of a presentation slide element."""

    TITLE = "title"
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    SHAPE = "shape"
    CONNECTOR = "connector"
    GROUP = "group"
    UNKNOWN = "unknown"


class ChartType(str, Enum):
    """Categorized chart types supported natively or inferred."""

    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    COMBINATION = "combination"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class ElementPosition(BaseModel):
    """Coordinates on the slide surface (measured in points or inches)."""

    model_config = ConfigDict(extra="ignore")

    left: float = 0.0
    top: float = 0.0


class ElementDimensions(BaseModel):
    """Dimensions on the slide surface (measured in points or inches)."""

    model_config = ConfigDict(extra="ignore")

    width: float = 0.0
    height: float = 0.0


class SlideTextRun(BaseModel):
    """Atomic text fragment with consistent character formatting."""

    model_config = ConfigDict(extra="ignore")

    text: str
    font_name: str | None = None
    font_size: float | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str | None = None


class SlideParagraph(BaseModel):
    """Paragraph with hierarchical bullet level and alignment."""

    model_config = ConfigDict(extra="ignore")

    text: str
    level: int = 0  # 0-indexed bullet nesting depth
    bullet: bool = False
    alignment: str | None = None  # left, center, right, justify
    runs: list[SlideTextRun] = Field(default_factory=list)


class ElementFormatting(BaseModel):
    """Visual style attributes of an element or shape."""

    model_config = ConfigDict(extra="ignore")

    fill_color: str | None = None
    border_color: str | None = None
    border_width: float | None = None
    opacity: float | None = None
    has_shadow: bool = False


class SlideTableCell(BaseModel):
    """Atomic cell representation in a presentation table."""

    model_config = ConfigDict(extra="ignore")

    row: int
    column: int
    text: str
    is_header: bool = False
    formatting: dict[str, Any] = Field(default_factory=dict)


class SlideTable(BaseModel):
    """Tabular data structure inside a slide."""

    model_config = ConfigDict(extra="ignore")

    table_id: str
    slide_id: str
    slide_number: int
    rows_count: int = 0
    columns_count: int = 0
    headers: list[str] = Field(default_factory=list)
    rows: list[list[SlideTableCell]] = Field(default_factory=list)
    merged_cells: list[dict[str, Any]] = Field(default_factory=list)
    has_header: bool = False


class SlideChartSeries(BaseModel):
    """Data series within a presentation chart."""

    model_config = ConfigDict(extra="ignore")

    name: str
    values: list[float | None] = Field(default_factory=list)


class SlideChart(BaseModel):
    """Native or inferred chart data extracted from a slide."""

    model_config = ConfigDict(extra="ignore")

    chart_id: str
    slide_id: str
    slide_number: int
    chart_type: ChartType = ChartType.UNKNOWN
    title: str | None = None
    axis_titles: dict[str, str] = Field(default_factory=dict)
    categories: list[str] = Field(default_factory=list)
    series: list[SlideChartSeries] = Field(default_factory=list)
    legends: list[str] = Field(default_factory=list)
    data_labels: list[str] = Field(default_factory=list)
    position: ElementPosition | None = None
    dimensions: ElementDimensions | None = None
    is_inferred: bool = False
    confidence: float = 1.0


class SlideAsset(BaseModel):
    """Extracted embedded image, picture, or media asset."""

    model_config = ConfigDict(extra="ignore")

    asset_id: str
    slide_id: str
    slide_number: int
    original_filename: str | None = None
    format: str  # png, jpeg, svg, etc.
    content_type: str = "image/png"
    sha256: str
    size_bytes: int = 0
    width: int | None = None
    height: int | None = None
    position: ElementPosition | None = None
    dimensions: ElementDimensions | None = None
    alt_text: str | None = None
    storage_path: str | None = None
    analysis_summary: dict[str, Any] | None = None


class DiagramNode(BaseModel):
    """Node in a reconstructed diagram."""

    model_config = ConfigDict(extra="ignore")

    node_id: str
    label: str
    shape_type: str = "rectangle"
    position: ElementPosition | None = None
    dimensions: ElementDimensions | None = None


class DiagramEdge(BaseModel):
    """Directed or undirected edge connecting diagram nodes."""

    model_config = ConfigDict(extra="ignore")

    edge_id: str
    source_id: str
    target_id: str
    label: str | None = None
    arrow_type: str | None = None


class SlideDiagram(BaseModel):
    """Reconstructed flow, flowchart, or diagram within a slide."""

    model_config = ConfigDict(extra="ignore")

    diagram_id: str
    slide_id: str
    slide_number: int
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    groups: list[dict[str, Any]] = Field(default_factory=list)


class Element(BaseModel):
    """Generic atomic slide element (text, shape, table, chart, image)."""

    model_config = ConfigDict(extra="ignore")

    element_id: str
    element_type: ElementType = ElementType.UNKNOWN
    text: str | None = None
    paragraphs: list[SlideParagraph] = Field(default_factory=list)
    position: ElementPosition = Field(default_factory=ElementPosition)
    dimensions: ElementDimensions = Field(default_factory=ElementDimensions)
    rotation: float = 0.0
    formatting: ElementFormatting = Field(default_factory=ElementFormatting)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    asset_reference: str | None = None
    source_provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    raw_data: dict[str, Any] | None = None


class Slide(BaseModel):
    """Single slide in a presentation with structure and element hierarchy."""

    model_config = ConfigDict(extra="ignore")

    slide_id: str
    slide_number: int  # 1-indexed
    title: str | None = None
    layout: str | None = None
    dimensions: ElementDimensions | None = None
    elements: list[Element] = Field(default_factory=list)
    speaker_notes: str | None = None
    hidden: bool = False
    background: dict[str, Any] | None = None
    reading_order: list[str] = Field(default_factory=list)


class PresentationDimensions(BaseModel):
    """Dimensions and aspect ratio of presentation slides."""

    model_config = ConfigDict(extra="ignore")

    width: float = 10.0
    height: float = 7.5
    aspect_ratio: str = "4:3"
    unit: str = "inches"


class PresentationMetadata(BaseModel):
    """Presentation-level administrative and structural metadata."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    subject: str | None = None
    author: str | None = None
    created_at: str | None = None
    modified_at: str | None = None
    language: str | None = None
    slide_count: int = 0
    hidden_slide_count: int = 0
    presentation_dimensions: PresentationDimensions = Field(default_factory=PresentationDimensions)
    theme: str | None = None
    layout_names: list[str] = Field(default_factory=list)
    embedded_media_count: int = 0
    properties: dict[str, Any] = Field(default_factory=dict)


class SpeakerNoteSummary(BaseModel):
    """Extracted speaker note for a slide."""

    model_config = ConfigDict(extra="ignore")

    slide_id: str
    slide_number: int
    text: str
    word_count: int = 0


class PresentationDocument(BaseModel):
    """Top-level canonical structured representation of an entire presentation."""

    model_config = ConfigDict(extra="ignore")

    document_id: str
    file_id: str
    format: str  # pptx, ppt, odp
    metadata: PresentationMetadata
    presentation_dimensions: PresentationDimensions = Field(default_factory=PresentationDimensions)
    slide_count: int = 0
    slides: list[Slide] = Field(default_factory=list)
    assets: list[SlideAsset] = Field(default_factory=list)
    charts: list[SlideChart] = Field(default_factory=list)
    tables: list[SlideTable] = Field(default_factory=list)
    diagrams: list[SlideDiagram] = Field(default_factory=list)
    speaker_notes: list[SpeakerNoteSummary] = Field(default_factory=list)
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    processing_status: str = "completed"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PresentationManifest(BaseModel):
    """Operational manifest recording execution metrics and generated artifact paths."""

    model_config = ConfigDict(extra="ignore")

    document_id: str
    file_id: str
    source_filename: str
    source_format: str
    status: str
    engine_name: str
    engine_version: str
    processing_time_seconds: float
    slide_count: int
    hidden_slide_count: int
    total_elements: int
    asset_count: int
    table_count: int
    chart_count: int
    diagram_count: int
    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PresentationCapabilities(BaseModel):
    """Platform capabilities and limits for presentation intelligence."""

    model_config = ConfigDict(extra="ignore")

    supported_formats: list[str] = ["pptx", "ppt", "odp"]
    max_upload_size_mb: int = 100
    max_slides_limit: int = 500
    max_shapes_per_slide: int = 2000
    native_pptx_supported: bool = True
    native_odp_supported: bool = True
    legacy_ppt_supported: bool = True
    chart_extraction_supported: bool = True
    diagram_extraction_supported: bool = True
    speaker_notes_supported: bool = True
    image_intelligence_integration: bool = True
