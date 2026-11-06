# Universal Conversion API Reference

DocuMind provides RESTful API endpoints for universal file format conversion, batch processing, status polling, preview retrieval, and artifact downloading.

---

## 1. Capabilities & Supported Formats

### `GET /api/v1/conversion/capabilities`
Returns the capability matrix across all supported input formats and allowed output conversions.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "input_format": "pdf",
      "category": "document",
      "display_name": "Portable Document Format",
      "description": "Portable Document Format extraction and universal conversion.",
      "supported_modes": ["plain_text", "structured_text", "complete"],
      "allowed_output_formats": ["txt", "md", "json", "html", "zip"],
      "supports_ocr": true
    }
  ],
  "meta": { "total_formats": 60 }
}
```

---

## 2. File Conversion Endpoints

### `POST /api/v1/conversions`
Uploads a file, automatically detects its format, extracts authentic content, and converts it to the requested target format.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (File, required): The source binary or text file to convert.
- `target_format` (string, default: `"txt"`): Target format (`txt`, `md`, `json`, `csv`, `html`, `zip`, `srt`, `vtt`).
- `extraction_mode` (string, default: `"structured_text"`): Mode (`plain_text`, `structured_text`, `complete`).
- `ocr_enabled` (boolean, default: `true`): Enable OCR for scanned documents and images.
- `preserve_tables` (boolean, default: `true`): Preserve tabular structures.
- `preserve_headings` (boolean, default: `true`): Preserve document section hierarchy.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "77f58e68-19d2-4d9d-9893-b59e95f00a1d",
    "status": "completed",
    "original_filename": "report.pdf",
    "source_format": "pdf",
    "target_format": "html",
    "extraction_mode": "structured_text",
    "progress_percent": 100.0,
    "output_filename": "report.html",
    "output_size_bytes": 3218,
    "mime_type": "text/html",
    "preview_content": "<!DOCTYPE html>...",
    "download_url": "/api/v1/conversions/77f58e68-19d2-4d9d-9893-b59e95f00a1d/download",
    "duration_seconds": 0.079,
    "warnings": [],
    "created_at": "2026-11-06T20:20:09.108Z",
    "completed_at": "2026-11-06T20:20:09.116Z"
  }
}
```

---

### `POST /api/v1/conversions/batch`
Submits multiple files for simultaneous conversion in a batch.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `files` (Array of Files, required): Multiple files to convert.
- `target_format` (string, default: `"txt"`): Target format.
- `extraction_mode` (string, default: `"structured_text"`): Extraction mode.
- `ocr_enabled` (boolean, default: `true`): Enable OCR.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1",
      "status": "completed",
      "output_filename": "file1.md"
    },
    {
      "id": "uuid-2",
      "status": "completed",
      "output_filename": "file2.md"
    }
  ],
  "meta": { "total": 2 }
}
```

---

## 3. Inspection & Download Endpoints

### `GET /api/v1/conversions/{conversion_id}`
Returns the metadata and progress status of a specific conversion job.

---

### `GET /api/v1/conversions/{conversion_id}/result`
Returns the generated preview snippet and metadata for immediate browser rendering.

---

### `GET /api/v1/conversions/{conversion_id}/download`
Streams the generated output file with appropriate `Content-Disposition` attachment headers and MIME type.

---

### `GET /api/v1/conversions/{conversion_id}/files`
Lists all individual files contained inside a Mode C extraction ZIP bundle or converted archive.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    { "filename": "report.txt", "size_bytes": 1200, "is_directory": false },
    { "filename": "report.md", "size_bytes": 1450, "is_directory": false },
    { "filename": "report.json", "size_bytes": 3500, "is_directory": false },
    { "filename": "tables/table_1.csv", "size_bytes": 450, "is_directory": false }
  ]
}
```

---

### `POST /api/v1/conversions/{conversion_id}/retry`
Re-queues a failed or completed conversion job.

---

### `DELETE /api/v1/conversions/{conversion_id}`
Permanently deletes the conversion database record and purges all generated artifacts from local storage.

---

### `GET /api/v1/conversion-history`
Retrieves a paginated list of all past conversions.

**Query Parameters**:
- `page` (integer, default: `1`): Page number (1-based).
- `limit` (integer, default: `20`): Page size (max: `100`).
- `status` (string, optional): Filter by `completed`, `processing`, or `failed`.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  }
}
```
