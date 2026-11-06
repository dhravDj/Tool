# DocuMind AI — Presentation Intelligence API Reference

Base URL: `/api/v1`

## 1. Capabilities Endpoint

### `GET /presentation-intelligence/capabilities`
Returns platform-level capabilities, supported presentation formats, upload boundaries, and feature availability.

**Response:**
```json
{
  "success": true,
  "data": {
    "supported_formats": ["odp", "ppt", "pptx"],
    "max_upload_size_mb": 100,
    "max_slides_limit": 500,
    "max_shapes_per_slide": 2000,
    "native_pptx_supported": true,
    "native_odp_supported": true,
    "legacy_ppt_supported": true,
    "chart_extraction_supported": true,
    "diagram_extraction_supported": true,
    "speaker_notes_supported": true,
    "image_intelligence_integration": true
  },
  "message": "Presentation intelligence capabilities retrieved."
}
```

---

## 2. Analysis Execution

### `POST /files/{file_id}/analyze-presentation`
Triggers presentation parsing, layout extraction, table, chart, asset, and speaker note extraction.

**Path Parameters:**
- `file_id` (UUID): Target persisted file identifier.

**Response (`PresentationManifest`):**
```json
{
  "success": true,
  "data": {
    "document_id": "pres_doc_a1b2c3d4e5f6",
    "file_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "source_filename": "strategy_deck.pptx",
    "source_format": "pptx",
    "status": "completed",
    "engine_name": "python-pptx",
    "engine_version": "1.0.2",
    "processing_time_seconds": 0.045,
    "slide_count": 12,
    "hidden_slide_count": 1,
    "total_elements": 48,
    "asset_count": 4,
    "table_count": 2,
    "chart_count": 1,
    "diagram_count": 1,
    "artifacts": {
      "json": "processed/.../presentation_document.json",
      "markdown": "processed/.../presentation_report.md",
      "text": "processed/.../presentation_text.txt",
      "manifest": "processed/.../presentation_manifest.json"
    },
    "warnings": []
  }
}
```

---

## 3. Data Retrieval Endpoints

### `GET /files/{file_id}/presentation-analysis`
Retrieves database metadata summary for the presentation analysis.

### `GET /files/{file_id}/presentation-analysis/result`
Retrieves the complete canonical `PresentationDocument` JSON.

### `GET /files/{file_id}/presentation-analysis/slides`
Retrieves a lightweight summary catalog of all slides in the presentation.

### `GET /files/{file_id}/presentation-analysis/slides/{slide_id}`
Retrieves detailed contents of a specific slide (including elements, tables, charts, diagrams, and speaker notes).

### `GET /files/{file_id}/presentation-analysis/assets`
Retrieves list of embedded pictures and visual assets.

### `GET /files/{file_id}/presentation-analysis/summary`
Returns high-level structural metrics and speaker notes overview.

---

## 4. Export & Download Endpoints

### `GET /files/{file_id}/presentation-analysis/export/{format}`
### `GET /files/{file_id}/presentation-analysis/download?format={format}`

**Supported Formats:**
- `json`: Canonical JSON presentation document.
- `markdown` / `md`: Formatted hierarchical Markdown report.
- `text` / `txt`: Plain text stream.
- `manifest`: Execution manifest JSON.
