# DocuMind AI — Archive Intelligence REST API

## 1. Overview

The Archive Intelligence API provides endpoints for inspecting, extracting, navigating, querying, and exporting archive files and nested file trees.

Base Route: `/api/v1`

---

## 2. Endpoints Reference

### Capabilities & Engine Metadata

#### `GET /api/v1/archive-intelligence/capabilities`
Returns supported formats, security limits, max nesting depth, and operational features.

**Response:**
```json
{
  "success": true,
  "data": {
    "supported_formats": ["zip", "7z", "tar", "tar.gz", "tgz", "gz", "tar.bz2", "tbz2", "tar.xz", "txz"],
    "max_nesting_depth": 5,
    "max_entries_per_archive": 10000,
    "max_single_file_size_bytes": 1073741824,
    "max_total_extracted_size_bytes": 5368709120,
    "features": ["safe_inspection", "zip_slip_defense", "bomb_protection", "recursive_nested_processing", "downstream_routing"]
  }
}
```

---

### Archive Processing & Analysis

#### `POST /api/v1/files/{file_id}/analyze-archive`
Executes archive analysis with configurable processing modes and optional decryption password.

**Request Body:**
```json
{
  "mode": "extract_and_analyze",
  "selected_entry_ids": null,
  "password": "optional_secret_password"
}
```

**Modes:**
- `inspect_only`: Generates entry manifest, hierarchy tree, and security audit without extracting.
- `extract_only`: Safely unpacks files into storage without running downstream intelligence.
- `extract_and_analyze`: Extracts files and runs matching intelligence pipelines (default).
- `selective`: Extracts and analyzes only the entry IDs specified in `selected_entry_ids`.

#### `POST /api/v1/files/{file_id}/archive-analysis/extract`
Shortcut to trigger Mode B (Extraction Only).

#### `POST /api/v1/files/{file_id}/archive-analysis/analyze-selected`
Shortcut to trigger Mode D (Selective Extraction and Analysis) for a list of entry IDs.

---

### Results & Query Endpoints

#### `GET /api/v1/files/{file_id}/archive-analysis`
Returns high-level summary overview from database (`ArchiveAnalysisRecord`).

#### `GET /api/v1/files/{file_id}/archive-analysis/result`
Returns full canonical `ArchiveDocument` with entries, hierarchy tree, and security report.

#### `GET /api/v1/files/{file_id}/archive-analysis/summary`
Returns concise statistical summary (file counts, compression ratios, safety verdict).

#### `GET /api/v1/files/{file_id}/archive-analysis/tree`
Returns hierarchical directory tree node representation.

#### `GET /api/v1/files/{file_id}/archive-analysis/entries`
Paginated search and filter for archive members.

**Query Parameters:**
- `skip`: Integer offset (default `0`).
- `limit`: Integer page limit (default `100`, max `1000`).
- `entry_type`: Filter by `"file"`, `"directory"`, `"symlink"`.
- `search`: Case-insensitive substring match on entry path or filename.

#### `GET /api/v1/files/{file_id}/archive-analysis/entries/{entry_id}`
Returns detailed metadata for an individual entry by entry ID.

#### `GET /api/v1/files/{file_id}/archive-analysis/nested-archives`
Lists all child archives discovered inside this archive.

#### `GET /api/v1/files/{file_id}/archive-analysis/children`
Lists all child files created from extraction, including their new `FileRecord` IDs and downstream engines.

#### `GET /api/v1/files/{file_id}/archive-analysis/security-report`
Returns the security and vulnerability assessment report.

#### `GET /api/v1/files/{file_id}/archive-analysis/extraction-status`
Returns extraction progress, current state, and error messages.

---

### Export & Download Endpoints

#### `GET /api/v1/files/{file_id}/archive-analysis/export/{format}`
Streams generated artifact files:
- `json`: Canonical `ArchiveDocument` JSON.
- `markdown`: Human-readable Markdown summary report.
- `text`: Plain text ASCII hierarchy overview.
- `manifest`: CSV table of all entries and checksums.
- `tree`: Visual ASCII directory tree.
- `extraction_report`: JSON extraction metrics and status.
- `security_report`: JSON security audit report.
- `child_manifest`: JSON mapping of extracted files to storage IDs.
