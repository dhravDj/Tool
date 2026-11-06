# DocuMind AI — Universal File Inspector Specification (Phase 13)

## 1. Executive Summary

The **Universal File Inspector** (`frontend/src/components/inspector/UniversalFileInspector.tsx`, route `/inspector/:fileId`) serves as DocuMind AI's centralized, multi-modal file examination workbench. Rather than requiring users to switch between disparate tools or sub-applications, the inspector adaptively selects and renders specialized intelligence viewers based on the file's validated format category.

---

## 2. Adaptive Engine Binding Matrix

When a file is loaded into the inspector, its `format_category` and `detection_format_id` dynamically bind to the appropriate specialized intelligence engine:

| Format Category | Target Component | Phase Provenance | Visualizer & Analysis Capabilities |
|---|---|---|---|
| `document` / `pdf` | `DocumentExtractionView` | Phase 3 | Formatted markdown preview, OCR page layout, table grid renderer, structural hierarchy |
| `spreadsheet` | `SpreadsheetIntelligenceView` | Phase 5 | Sheet selector tabs, cell grid, formula dependency analysis, numerical statistics, anomalies |
| `presentation` | `PresentationIntelligenceView` | Phase 6 | Slide-by-slide thumbnail strip, presentation outlines, speaker notes, extracted vector diagrams |
| `image` | `ImageIntelligenceView` | Phase 4 | High-resolution image canvas, OCR bounding box overlay, color histogram, EXIF camera details |
| `audio` | `AudioIntelligenceView` | Phase 7 | Interactive waveform track, speaker diarization tags, synchronized transcript playback |
| `video` | `VideoIntelligenceView` | Phase 8 | Keyframe timeline carousel, scene detection breakdown, aligned speech transcript |
| `code` | `CodeIntelligenceView` | Phase 9 | Syntax-highlighted code editor view, AST symbol tree, import dependency graph, complexity score |
| `structured_data` | `StructuredDataIntelligenceView`| Phase 9 | Interactive tree/JSON view, schema validation report, tabular view for Parquet/CSV data |
| `archive` | `ArchiveIntelligenceView` | Phase 10 | Nested folder/file tree viewer, uncompressed size ratio, security alerts (zip bomb / path traversal) |

---

## 3. Inspector Layout & Header Architecture

The inspector header provides essential metadata and immediate user actions:
- **File Identity**: Original filename, format pill badge, file size in human units (`1 MB`, `450 KB`), and the responsible extraction engine version.
- **AI Vector Status**: Inline indicator verifying whether the file is indexed (`AI Indexed (X chunks)`) or unindexed (`Not Indexed`).
- **Immediate Action Toolbar**:
  - `Index for AI`: Dispatches `POST /ai/index/{fileId}` with asynchronous spinner and automatic cache invalidation.
  - `Download`: Direct hyperlink to `GET /api/v1/files/{fileId}/download`.
  - `Close Inspector`: Dismisses modal state when embedded in the File Library.

---

## 4. Sub-Tab Architecture

The Universal File Inspector contains three integrated tabs:

```
[ Intelligence Analysis ]     [ Chat & Ask AI ]     [ File Metadata & Hashes ]
```

### 4.1 Tab 1: Intelligence Analysis
Renders the dedicated format viewer as outlined in Section 2, ensuring that all extraction signals (tables, audio waves, slide notes, code AST) are directly accessible.

### 4.2 Tab 2: Chat & Ask AI
Pre-scopes the conversational RAG workspace (`AIWorkspace`) to this specific file. The conversation is initiated with the document pre-selected as grounding context, allowing users to ask instant questions (e.g. *"What is the total expenditure mentioned in section 3?"* or *"Summarize slide 5"*).

### 4.3 Tab 3: File Metadata & Hashes
Presents zero-trust security and storage verification:
- Cryptographic SHA-256 hash with one-click copy button.
- Registered storage path on disk.
- Exact detected MIME type vs claimed file extension.
- Confidence score and detection evidence signals (magic numbers, container inspection).
- Ingestion and last updated timestamps.
