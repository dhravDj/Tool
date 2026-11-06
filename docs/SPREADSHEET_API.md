# DocuMind AI — Spreadsheet Intelligence REST API Reference

The Spreadsheet Intelligence API provides endpoints for triggering analysis, fetching canonical representations, downloading exported artifacts (CSV, XLSX, Parquet), and inspecting platform limits.

**Base Path:** `/api/v1`

---

## 1. Capabilities & Health

### `GET /api/v1/spreadsheet-intelligence/capabilities`
Returns supported formats, platform constraints, and engine feature flags.

#### Response `200 OK`
```json
{
  "supported_formats": ["xlsx", "xls", "csv", "tsv", "ods"],
  "max_upload_size_mb": 100,
  "max_rows_limit": 1000000,
  "max_columns_limit": 16384,
  "formula_extraction_supported": true,
  "formula_execution_allowed": false,
  "parquet_export_available": false,
  "supported_encodings": ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin1"]
}
```

---

## 2. Triggering Analysis

### `POST /api/v1/files/{file_id}/analyze-spreadsheet`
Triggers synchronous or queued spreadsheet intelligence analysis on an uploaded file record.

#### Path Parameters
- `file_id` (UUID, required): The ID of the uploaded file record.

#### Query Parameters
- `extract_formulas` (bool, default: `true`): Parse and categorize cell formulas.
- `profile_data` (bool, default: `true`): Generate statistical profiles and detect primary keys.
- `generate_artifacts` (bool, default: `true`): Create JSON, Markdown, CSV, and XLSX export artifacts.

#### Response `200 OK`
```json
{
  "file_id": "239b940e-2d93-41bb-9271-e9408b0213f0",
  "document_id": "f83a0424-9b1b-4f93-bc42-6e2101e14589",
  "status": "completed",
  "sheet_count": 3,
  "total_cells": 53,
  "formula_count": 9,
  "processing_duration_ms": 11.9,
  "manifest": { ... }
}
```

---

## 3. Retrieving Analysis Records & Status

### `GET /api/v1/files/{file_id}/spreadsheet-analysis`
Fetches the database record and execution status of the analysis.

#### Response `200 OK`
```json
{
  "id": "119b940e-2d93-41bb-9271-e9408b0213aa",
  "file_id": "239b940e-2d93-41bb-9271-e9408b0213f0",
  "status": "completed",
  "sheet_count": 3,
  "total_rows": 12,
  "total_cells": 53,
  "formula_count": 9,
  "execution_time_ms": 11.9,
  "created_at": "2026-11-06T11:30:00Z"
}
```

---

## 4. Canonical Document & Manifest

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/result`
Fetches the full canonical `SpreadsheetDocument` containing all worksheets, rows, cells, and profiling findings.

#### Response `200 OK`
Returns the serialized JSON document adhering to `SpreadsheetDocument` schema.

---

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/manifest`
Fetches the operational `SpreadsheetManifest` containing execution timings and links to all generated export artifacts.

---

## 5. Sheet-Level Inspection

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/sheets/{sheet_name_or_id}`
Retrieves data for a single worksheet tab with optional pagination.

#### Path Parameters
- `file_id` (UUID): Target file identifier.
- `sheet_name_or_id` (string): Either the sheet ID (e.g. `ws-1`) or exact sheet name (e.g. `Q1_Sales`).

#### Query Parameters
- `limit_rows` (int, default: `100`): Maximum rows to return.
- `offset_rows` (int, default: `0`): Row offset for pagination.

---

## 6. Multi-Format Exports

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/export/csv`
Downloads an RFC 4180 CSV export of a designated worksheet with formula injection sanitization.

#### Query Parameters
- `sheet` (string, optional): Target sheet name or index. Defaults to primary sheet.
- `sanitize` (bool, default: `true`): Prepends `'` to dangerous formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`).

#### Response Headers
- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="Q1_Sales.csv"`

---

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/export/xlsx`
Downloads a reconstructed multi-sheet Excel `.xlsx` workbook.

#### Response Headers
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="reconstructed_workbook.xlsx"`

---

### `GET /api/v1/files/{file_id}/spreadsheet-analysis/export/parquet`
Downloads an Apache Parquet binary file for a specified worksheet (if `pyarrow` is available).

#### Response Headers
- `Content-Type: application/octet-stream`
- `Content-Disposition: attachment; filename="sheet.parquet"`
