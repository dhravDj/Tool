# DocuMind AI — Presentation Canonical Schema Specification

## 1. Schema Hierarchy

The presentation intelligence schema provides a normalized, strongly-typed representation of presentations regardless of whether the source file was PPTX, PPT, or ODP.

```
PresentationDocument
 ├── PresentationMetadata
 ├── PresentationDimensions
 ├── Slide[]
 │    ├── Element[]
 │    │    ├── SlideParagraph[]
 │    │    │    └── SlideTextRun[]
 │    │    ├── ElementPosition
 │    │    └── ElementDimensions
 │    └── SpeakerNote (string)
 ├── SlideTable[]
 │    └── SlideTableCell[][]
 ├── SlideChart[]
 │    └── SlideChartSeries[]
 ├── SlideAsset[]
 ├── SlideDiagram[]
 │    ├── DiagramNode[]
 │    └── DiagramEdge[]
 ├── SpeakerNoteSummary[]
 └── ExtractionMetadata
```

---

## 2. Pydantic Model Definitions

### 2.1 `PresentationDocument`
```python
class PresentationDocument(BaseModel):
    document_id: str
    file_id: str
    format: str                         # "pptx", "ppt", "odp"
    metadata: PresentationMetadata
    presentation_dimensions: PresentationDimensions
    slide_count: int
    slides: list[Slide]
    assets: list[SlideAsset]
    charts: list[SlideChart]
    tables: list[SlideTable]
    diagrams: list[SlideDiagram]
    speaker_notes: list[SpeakerNoteSummary]
    extraction_metadata: dict[str, Any]
    warnings: list[str]
    confidence: float                   # 0.0 to 1.0
    processing_status: str              # "completed", "partial", "failed"
    created_at: str
```

### 2.2 `Slide`
```python
class Slide(BaseModel):
    slide_id: str
    slide_number: int                   # 1-indexed
    title: str | None = None
    layout: str | None = None
    dimensions: ElementDimensions | None = None
    elements: list[Element]
    speaker_notes: str | None = None
    hidden: bool = False
    background: dict[str, Any] | None = None
    reading_order: list[str]            # Ordered list of element_ids
```

### 2.3 `Element`
```python
class Element(BaseModel):
    element_id: str
    element_type: ElementType            # TITLE, TEXT, TABLE, CHART, IMAGE, SHAPE, CONNECTOR, GROUP
    text: str | None = None
    paragraphs: list[SlideParagraph]
    position: ElementPosition           # left, top (inches)
    dimensions: ElementDimensions       # width, height (inches)
    rotation: float = 0.0
    formatting: ElementFormatting
    relationships: list[dict[str, Any]]
    asset_reference: str | None = None
    source_provenance: dict[str, Any]
    confidence: float = 1.0
    raw_data: dict[str, Any] | None = None
```

### 2.4 `SlideTable`
```python
class SlideTable(BaseModel):
    table_id: str
    slide_id: str
    slide_number: int
    rows_count: int
    columns_count: int
    headers: list[str]
    rows: list[list[SlideTableCell]]
    merged_cells: list[dict[str, Any]]
    has_header: bool
```

### 2.5 `SlideChart`
```python
class SlideChart(BaseModel):
    chart_id: str
    slide_id: str
    slide_number: int
    chart_type: ChartType               # BAR, COLUMN, LINE, PIE, DOUGHNUT, AREA, SCATTER, RADAR, etc.
    title: str | None = None
    axis_titles: dict[str, str]
    categories: list[str]
    series: list[SlideChartSeries]
    legends: list[str]
    data_labels: list[str]
    position: ElementPosition | None = None
    dimensions: ElementDimensions | None = None
    is_inferred: bool = False
    confidence: float = 1.0
```

### 2.6 `SlideAsset`
```python
class SlideAsset(BaseModel):
    asset_id: str
    slide_id: str
    slide_number: int
    original_filename: str | None = None
    format: str                         # "png", "jpeg", "svg"
    content_type: str
    sha256: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    position: ElementPosition | None = None
    dimensions: ElementDimensions | None = None
    alt_text: str | None = None
    storage_path: str | None = None
```

### 2.7 `SlideDiagram`
```python
class SlideDiagram(BaseModel):
    diagram_id: str
    slide_id: str
    slide_number: int
    nodes: list[DiagramNode]            # node_id, label, shape_type, position, dimensions
    edges: list[DiagramEdge]            # edge_id, source_id, target_id, label, arrow_type
    groups: list[dict[str, Any]]
```
