# DocuMind AI — Canonical Image Processing Schema

**Specification Version:** 1.0.0  
**Schema Implementation:** `app.modules.image_intelligence.schemas.image_document`  

---

## 1. Schema Hierarchy

Every processed image yields a standardized `ImageDocument` AST object containing:
- `metadata`: Technical attributes, dimensions, color profiles, sanitized EXIF.
- `analysis`: High-level AI scene caption, scene type, dominant colors, diagram analysis, chart analysis, OCR text stream.
- `regions`: Array of localized bounding box annotations (`ImageRegion`).
- `preprocessed_artifacts`: Dictionary of applied pipeline transformations.
- `warnings`: Pipeline diagnostic and warning strings.

```
ImageDocument
├── image_id: str
├── file_id: str
├── filename: str
├── metadata: ImageMetadata
├── analysis: ImageAnalysis
│   ├── caption: str
│   ├── scene_type: str
│   ├── detected_objects: list[str]
│   ├── dominant_colors: list[str]
│   ├── diagram: DiagramAnalysis
│   ├── chart: ChartAnalysis
│   ├── ocr_full_text: str
│   ├── ocr_word_count: int
│   └── ocr_average_confidence: float
└── regions: list[ImageRegion]
```

---

## 2. Coordinate System Specification

DocuMind AI utilizes two complementary coordinate representations:

### 1. Normalized Bounding Box (`bounding_box`)
- Format: `[ymin, xmin, ymax, xmax]`
- Data Type: Floating point numbers in the closed interval $[0.0, 1.0]$
- Origin: Top-left corner of the image is `(0.0, 0.0)`; bottom-right corner is `(1.0, 1.0)`.
- Use Case: Responsive frontend UI rendering across varied viewport sizes, canvas overlays, and model grounding.

### 2. Exact Pixel Box (`pixel_box`)
- Format: `[x0, y0, x1, y1]`
- Data Type: Integer pixel offsets
- Origin: Top-left coordinate `(x0, y0)`, bottom-right coordinate `(x1, y1)`.
- Use Case: Cropping, sub-region OCR re-processing, and high-precision image transformations.

---

## 3. Schema Definitions

### 3.1 `ImageMetadata`
```typescript
interface ImageMetadata {
  format: string;             // "png", "jpeg", "webp", "tiff", "bmp", "svg"
  width: number;              // Pixel width
  height: number;             // Pixel height
  aspect_ratio: number;       // width / height (e.g. 1.33)
  color_mode: string;         // "RGB", "RGBA", "L", "CMYK", "Vector/RGBA"
  channels: number;           // Channel count (e.g. 3 or 4)
  bit_depth: number;          // Bit depth (e.g. 8, 24, 32)
  file_size: number;          // File size in bytes
  dpi?: [number, number];     // Horizontal and vertical DPI
  has_transparency: boolean;  // True if alpha channel is active
  is_animated: boolean;       // True for multi-frame GIF/WEBP/PNG
  frame_count: number;        // Frame count (default 1)
  duration_ms?: number;       // Animation frame duration
  exif_scrubbed: Record<string, unknown>; // Safe EXIF parameters
  gps_redacted: boolean;      // Guaranteed true (privacy compliance)
}
```

### 3.2 `ImageRegion`
```typescript
interface ImageRegion {
  region_id: string;          // Unique region identifier (e.g. "text_word_1")
  region_type: RegionType;    // "text" | "object" | "diagram" | "chart" | "table" | "face" | "background"
  bounding_box: [number, number, number, number]; // [ymin, xmin, ymax, xmax]
  pixel_box?: [number, number, number, number];   // [x0, y0, x1, y1]
  label: string;              // Semantic descriptor or class
  text?: string | null;       // Recognized OCR text if region_type === "text"
  confidence: number;         // Confidence score (0.0 to 1.0)
  provenance: string;         // "ocr" | "object-detector" | "diagram-parser" | "chart-parser"
  reading_order?: number;     // Positional sequence in text stream
  attributes: Record<string, unknown>;
}
```

### 3.3 `DiagramAnalysis`
```typescript
interface DiagramAnalysis {
  is_diagram: boolean;
  diagram_type: string;       // "flowchart" | "sequence" | "architecture" | "hierarchy" | "none"
  nodes: Array<{
    node_id: string;
    label: string;
    shape?: string;
    bounding_box?: number[];
  }>;
  connectors_count: number;
  flow_direction: string;     // "top-to-bottom" | "left-to-right" | "radial" | "unknown"
  confidence: number;
}
```

### 3.4 `ChartAnalysis`
```typescript
interface ChartAnalysis {
  is_chart: boolean;
  chart_type: string;         // "bar" | "line" | "pie" | "scatter" | "none"
  title?: string | null;
  x_axis_label?: string | null;
  y_axis_label?: string | null;
  legend_items: string[];
  series_data: Array<{
    label?: string;
    value?: number;
    unit?: string;
  }>;
  confidence: number;
}
```
