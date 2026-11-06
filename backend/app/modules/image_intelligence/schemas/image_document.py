"""Pydantic v2 Canonical Schemas for Image & Visual Intelligence Engine."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RegionType(str, Enum):
    """Semantic classification of an image bounding box region."""

    TEXT = "text"
    OBJECT = "object"
    DIAGRAM = "diagram"
    CHART = "chart"
    TABLE = "table"
    FACE = "face"
    BACKGROUND = "background"


class ImageMetadata(BaseModel):
    """Rich image technical properties, color metrics, and privacy-sanitized EXIF."""

    model_config = ConfigDict(extra="ignore")

    format: str
    width: int
    height: int
    aspect_ratio: float
    color_mode: str
    channels: int
    bit_depth: int
    file_size: int
    dpi: tuple[float, float] | None = None
    has_transparency: bool = False
    is_animated: bool = False
    frame_count: int = 1
    duration_ms: int | None = None
    exif_scrubbed: dict[str, Any] = Field(default_factory=dict)
    gps_redacted: bool = True


class ImageRegion(BaseModel):
    """Normalized bounding box region within an image with semantic labels and provenance."""

    model_config = ConfigDict(extra="ignore")

    region_id: str
    region_type: RegionType
    # Normalized coordinates [ymin, xmin, ymax, xmax] from 0.0 to 1.0
    bounding_box: list[float]
    # Exact pixel boundaries [x0, y0, x1, y1]
    pixel_box: list[int] | None = None
    label: str
    text: str | None = None
    confidence: float = 1.0
    provenance: str = (
        "native"  # "ocr", "model-caption", "object-detector", "diagram-parser", "chart-parser"
    )
    reading_order: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class DiagramAnalysis(BaseModel):
    """Structural flow and component analysis for technical diagrams and schematics."""

    model_config = ConfigDict(extra="ignore")

    is_diagram: bool = False
    diagram_type: str = "none"  # "flowchart", "sequence", "architecture", "hierarchy", "none"
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    connectors_count: int = 0
    flow_direction: str = "unknown"  # "top-to-bottom", "left-to-right", "radial", "unknown"
    confidence: float = 0.0


class ChartAnalysis(BaseModel):
    """Data series and graphical properties extracted from statistical charts."""

    model_config = ConfigDict(extra="ignore")

    is_chart: bool = False
    chart_type: str = "none"  # "bar", "line", "pie", "scatter", "none"
    title: str | None = None
    x_axis_label: str | None = None
    y_axis_label: str | None = None
    legend_items: list[str] = Field(default_factory=list)
    series_data: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


class ImageAnalysis(BaseModel):
    """Consolidated visual intelligence output across vision models, OCR, and analyzers."""

    model_config = ConfigDict(extra="ignore")

    caption: str = ""
    scene_type: str = "general"
    detected_objects: list[str] = Field(default_factory=list)
    dominant_colors: list[str] = Field(default_factory=list)
    diagram: DiagramAnalysis = Field(default_factory=DiagramAnalysis)
    chart: ChartAnalysis = Field(default_factory=ChartAnalysis)
    ocr_full_text: str = ""
    ocr_word_count: int = 0
    ocr_average_confidence: float = 0.0


class ImageDocument(BaseModel):
    """Canonical representation of an analyzed image document."""

    model_config = ConfigDict(extra="ignore")

    image_id: str
    file_id: str
    filename: str
    metadata: ImageMetadata
    analysis: ImageAnalysis
    regions: list[ImageRegion] = Field(default_factory=list)
    preprocessed_artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ImageManifest(BaseModel):
    """Operational execution manifest recording pipeline runtime, engines, and artifacts."""

    model_config = ConfigDict(extra="ignore")

    image_id: str
    file_id: str
    filename: str
    status: str
    processing_time_seconds: float
    engines_used: dict[str, str]
    artifacts: dict[str, str]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class VisionModelCapabilities(BaseModel):
    """Platform vision intelligence hardware and model capabilities."""

    model_config = ConfigDict(extra="ignore")

    supported_formats: list[str]
    ocr_engine: str
    ocr_available: bool
    default_vision_engine: str
    available_vision_engines: list[str]
    hardware_acceleration: str
    max_image_dimension_px: int
    privacy_gps_scrubbing: bool = True
    preprocessing_steps: list[str]


class ImageAskRequest(BaseModel):
    """Request payload for Visual Question Answering (VQA) on an analyzed image."""

    model_config = ConfigDict(extra="ignore")

    question: str
    focus_region_id: str | None = None


class ImageAskResponse(BaseModel):
    """Answer payload for Visual Question Answering with grounding evidence."""

    model_config = ConfigDict(extra="ignore")

    question: str
    answer: str
    confidence: float
    grounding_region_ids: list[str] = Field(default_factory=list)
    reasoning: str | None = None


class ImageAnalysisStatusResponse(BaseModel):
    """Summary status of image intelligence artifacts for a given file."""

    model_config = ConfigDict(extra="ignore")

    file_id: str
    status: str
    format: str
    width: int
    height: int
    color_mode: str
    ocr_word_count: int
    detected_objects_count: int
    has_charts: bool
    has_diagrams: bool
    artifacts: dict[str, str]
    manifest: ImageManifest | None = None
