# DocuMind AI — Image & Visual Intelligence Architecture

**Module:** `backend/app/modules/image_intelligence/`  
**Platform Version:** 0.4.0  
**Status:** Production Ready  

---

## 1. High-Level Architectural Overview

The **Image & Visual Intelligence Engine** provides comprehensive visual processing, structural understanding, optical character recognition (OCR), and visual question answering (VQA) across standalone image files and images extracted from compound documents (PDF, DOCX, EPUB, ODT).

```
                      +-----------------------------------+
                      |   Ingested Image or Document Asset|
                      |   (PNG, JPEG, WEBP, TIFF, BMP, SVG)|
                      +-----------------+-----------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
     [1. Metadata Extraction]                      [2. Non-Destructive Preprocessing]
     - Dimensions, Aspect Ratio                    - EXIF Orientation Auto-Correction
     - Color Space & Bit Depth                     - Normalization (bounds check)
     - Safe EXIF Parsing                           - Projection Deskewing
     - GPS & Privacy Sanitization                  - Otsu Adaptive Binarization
                 |                                 - Large Image Overlapping Tiling
                 |                                             |
                 +----------------------+----------------------+
                                        |
                                        v
                            [3. Vision & OCR Engines]
     +----------------------------------+----------------------------------+
     |                                  |                                  |
     v                                  v                                  v
[3a. OCR Subsystem]           [3b. Vision Understanding]      [3c. Structural Analyzers]
- Word & Line Coordinates     - Scene Classification          - Diagram / Flowchart Parser
- Reading Order Sorting       - Caption Generation            - Chart & Series Analyzer
- Confidence Metrics          - Object Contours & Labels      - Node & Flow Direction
- Low-Confidence Flagging     - Dominant Palette (Hex)        - Axis & Data Extractor
     |                                  |                                  |
     +----------------------------------+----------------------------------+
                                        |
                                        v
                        [4. Canonical ImageDocument AST]
                        - Unified Region Coordinates
                        - Full Provenance Tracking
                                        |
                                        v
                         [5. Output Generators & Storage]
                        - image_document.json
                        - image_report.md
                        - image_manifest.json
                        - ocr_text.txt
                        - Database Tracking (image_analysis_records)
```

---

## 2. Core Processing Stages

### Stage 1: Metadata Extraction & Privacy Sanitization (`metadata/extractor.py`)
- **Decompression Bomb Protection:** Enforces `PIL.Image.MAX_IMAGE_PIXELS = 89_478_485` (~89 MP ceiling), rejecting pixel flood attacks before allocating memory.
- **Format Specialization:**
  - Raster formats (PNG, JPEG, WEBP, TIFF, BMP) are parsed via Pillow.
  - Vector formats (SVG) are parsed safely using `defusedxml.ElementTree` without entity expansion or network calls.
- **Privacy Sanitization:**
  - Strips sensitive EXIF tags (GPS coordinates `0x8825`, camera serial numbers, lens serials, owner names).
  - Retains non-sensitive technical parameters (camera make/model, orientation, exposure datetime, software version).
  - `gps_redacted: true` is verified in the canonical metadata schema.

### Stage 2: Non-Destructive Image Preprocessing (`preprocessing/pipeline.py`)
- **Zero Mutation Guarantee:** Original files remain strictly unmodified in immutable storage; preprocessing produces working derivatives.
- **Orientation Correction:** Automatically applies EXIF orientation flags (`ImageOps.exif_transpose`).
- **Deskewing:** Employs horizontal projection profile variance across a $[-15^\circ, +15^\circ]$ search window to detect text skew and straightens documents with bicubic interpolation.
- **Grayscale & Contrast Enhancement:** Applies Auto-contrast and unsharp masking (`radius=1.5, percent=120, threshold=3`).
- **Otsu Binarization:** Maximizes inter-class variance between foreground glyphs and background paper for optimal OCR accuracy.
- **Large Image Tiling:** Images exceeding 1536px are segmented into overlapping grid tiles ($10\%$ horizontal/vertical overlap) with global coordinate re-projection.

### Stage 3: Optical Character Recognition Subsystem (`ocr/engine.py`)
- **Engine:** PyTesseract with asynchronous execution (`asyncio.to_thread`) to avoid blocking FastAPI's event loop.
- **Bounding Boxes:** Extracts word-level and line-level bounding boxes normalized to $[ymin, xmin, ymax, xmax]$ ($0.0$ to $1.0$).
- **Reading Order Reconstruction:** Groups words by vertical alignment thresholds and sorts lines top-to-bottom and left-to-right.
- **Graceful Fallback:** If Tesseract is not present on the host environment, reports clear diagnostics without crashing, returning empty text with informational warnings.

### Stage 4: Vision Scene Understanding (`vision/engine.py`)
- **Hardware Optimization:** Designed specifically for host hardware (AMD Ryzen 7 5800H + NVIDIA RTX 3050 4GB VRAM). Uses lightweight CPU inference with zero risk of GPU OOM errors.
- **Capabilities:**
  - Descriptive natural language captioning.
  - Scene categorization (`document_page`, `technical_diagram`, `statistical_chart`, `photo_or_artwork`).
  - Salient object detection with bounding box coordinates.
  - Dominant color palette extraction via spatial downsampling and histogram quantization.
  - Grounded Visual Question Answering (VQA) with explicit region attribution.

### Stage 5: Structural Diagram & Chart Analyzers (`diagrams/`, `charts/`)
- **Diagrams:** Identifies flowcharts, sequence diagrams, and architecture schematics, isolating discrete nodes, calculating flow direction (top-to-bottom, left-to-right), and enumerating connectors.
- **Charts:** Recognizes bar charts, line plots, and pie graphs, extracting titles, axes, legends, and reconstructing numerical data series.

---

## 3. Storage Hierarchy & Artifact Layout

Artifacts are persisted in the isolated filesystem path:
```
storage/processed/{file_id}/image/
├── image_document.json      # Canonical AST schema with all regions
├── image_report.md          # Human-readable Markdown summary with tables
├── image_manifest.json      # Execution manifest with engine versions & timings
└── ocr_text.txt             # Clean recognized text in reading order
```

---

## 4. Hardware Acceleration & Concurrency Guidelines

- **CPU Default:** All core operations execute via optimized C-extensions (NumPy, Pillow, libmagic) utilizing multi-core CPU threads.
- **GPU Scaling:** When NVIDIA CUDA or TensorRT is enabled with larger VRAM (> 8GB), modular adapters can be loaded dynamically without modifying pipeline interfaces.
