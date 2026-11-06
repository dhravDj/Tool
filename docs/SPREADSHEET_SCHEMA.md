# DocuMind AI — Spreadsheet Intelligence Schema Specification

**Schema Version:** `1.0.0`  
**Namespace:** `app.modules.spreadsheet_intelligence.schemas.spreadsheet_document`

This document specifies the canonical data contract for spreadsheet documents parsed and analyzed by DocuMind AI.

---

## 1. Top-Level Entity: `SpreadsheetDocument`

```json
{
  "document_id": "string (uuid)",
  "file_id": "string (uuid)",
  "schema_version": "1.0.0",
  "workbook_metadata": { ... },
  "worksheets": [ { ... } ],
  "defined_names": [ { ... } ],
  "relationships": [ { ... } ],
  "assets": [ { ... } ],
  "warnings": [ "string" ],
  "extraction_metadata": { ... },
  "created_at": "2026-11-06T12:00:00Z"
}
```

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `document_id` | `string` | Unique identifier for this analysis artifact. |
| `file_id` | `string` | Reference to the parent `FileRecord`. |
| `schema_version` | `string` | Canonical schema version (`"1.0.0"`). |
| `workbook_metadata` | `WorkbookMetadata` | Administrative and technical metadata of the workbook. |
| `worksheets` | `list[WorksheetData]` | Ordered list of worksheets in the workbook. |
| `defined_names` | `list[DefinedName]` | Named ranges and workbook-level expressions. |
| `relationships` | `list[dict]` | Cross-sheet and inter-table dependencies. |
| `assets` | `list[dict]` | Extracted images, shapes, or attachments. |
| `warnings` | `list[str]` | Non-fatal extraction warnings (e.g. truncated rows). |
| `extraction_metadata` | `dict` | Execution timing, engine version, and options. |
| `created_at` | `string` | ISO 8601 creation timestamp. |

---

## 2. Component Schemas

### 2.1 `WorkbookMetadata`
Describes workbook-level properties.

```json
{
  "filename": "quarterly_sales.xlsx",
  "format": "xlsx",
  "creator": "Financial Analyst",
  "last_modified_by": "Auditor",
  "created_at": "2026-01-15T09:30:00Z",
  "modified_at": "2026-03-31T17:45:00Z",
  "sheet_count": 3,
  "calculation_settings": {
    "calculation_mode": "auto",
    "iterative_calculation": false
  },
  "properties": {}
}
```

### 2.2 `WorksheetData`
Represents an individual worksheet tab.

```json
{
  "sheet_id": "ws-1",
  "name": "Q1_Sales",
  "position": 1,
  "visibility": "visible",
  "dimensions": "A1:F100",
  "total_rows": 100,
  "total_columns": 6,
  "merged_ranges": ["A1:F1"],
  "columns": [ ... ],
  "rows": [ ... ],
  "tables": [ ... ],
  "charts": [ ... ],
  "validations": [ ... ],
  "conditional_formats": [ ... ],
  "profiling": { ... }
}
```

- `visibility`: Enum: `"visible"`, `"hidden"`, `"very_hidden"`.
- `merged_ranges`: List of cell range coordinate strings (e.g. `["A1:D1", "B5:B8"]`).

### 2.3 `RowData` and `CellData` (Sparse Storage)
To prevent massive memory overhead, rows contain only populated, non-empty cells.

```json
{
  "row_index": 3,
  "height": 18.5,
  "is_hidden": false,
  "cells": [
    {
      "address": "A3",
      "row": 3,
      "column": 1,
      "raw_value": "TXN-1001",
      "formatted_value": "TXN-1001",
      "data_type": "text",
      "formula": null,
      "cached_value": null,
      "style": {
        "font_name": "Calibri",
        "font_size": 11.0,
        "bold": false,
        "italic": false,
        "underline": false,
        "font_color": "#000000",
        "fill_color": null,
        "horizontal_align": "left",
        "vertical_align": "center",
        "number_format": "@",
        "has_border": false
      },
      "hyperlink": null,
      "comment": null
    },
    {
      "address": "E3",
      "row": 3,
      "column": 5,
      "raw_value": 6000.0,
      "formatted_value": "$6,000.00",
      "data_type": "number",
      "formula": "=C3*D3",
      "cached_value": 6000.0,
      "style": {
        "number_format": "$#,##0.00"
      }
    }
  ]
}
```

#### `CellDataType` Enum
- `"empty"`: Empty cell with formatting only.
- `"text"`: String or unicode character sequence.
- `"number"`: Integer or floating-point value.
- `"boolean"`: Boolean `true` or `false`.
- `"date"`: ISO 8601 date or datetime.
- `"formula"`: Calculated formula expression.
- `"error"`: Spreadsheet error code (e.g., `#N/A`, `#DIV/0!`, `#VALUE!`).

---

## 3. Data Understanding & Profiling Schema (`WorksheetProfiling`)

```json
{
  "total_rows": 100,
  "total_columns": 6,
  "populated_cells": 580,
  "empty_rows_count": 0,
  "duplicate_rows_count": 0,
  "candidate_primary_keys": ["Transaction_ID"],
  "column_profiles": [
    {
      "column_index": 1,
      "column_letter": "A",
      "column_name": "Transaction_ID",
      "inferred_type": "text",
      "total_count": 100,
      "null_count": 0,
      "unique_count": 100,
      "min_value": "TXN-001",
      "max_value": "TXN-100",
      "mean": null,
      "median": null,
      "std_dev": null,
      "is_candidate_key": true,
      "frequent_values": []
    },
    {
      "column_index": 5,
      "column_letter": "E",
      "column_name": "Revenue",
      "inferred_type": "currency",
      "total_count": 100,
      "null_count": 0,
      "unique_count": 84,
      "min_value": 150.0,
      "max_value": 45000.0,
      "mean": 12845.50,
      "median": 10200.0,
      "std_dev": 8940.22,
      "is_candidate_key": false,
      "frequent_values": []
    }
  ]
}
```

---

## 4. Execution Manifest Schema (`SpreadsheetManifest`)

```json
{
  "document_id": "f83a0424-9b1b-4f93-bc42-6e2101e14589",
  "file_id": "239b940e-2d93-41bb-9271-e9408b0213f0",
  "source_filename": "sales.xlsx",
  "source_format": "xlsx",
  "status": "completed",
  "engine_name": "spreadsheet_intelligence_pipeline",
  "engine_version": "1.0.0",
  "processing_time_seconds": 0.012,
  "worksheet_count": 3,
  "total_rows": 12,
  "total_columns": 6,
  "total_cells": 53,
  "formula_count": 9,
  "artifacts": {
    "canonical_json": "storage/processed/239b.../spreadsheet_document.json",
    "markdown_report": "storage/processed/239b.../spreadsheet_report.md",
    "sheet_1_csv": "storage/processed/239b.../sheet_1.csv",
    "sheet_2_csv": "storage/processed/239b.../sheet_2.csv",
    "reconstructed_xlsx": "storage/processed/239b.../reconstructed.xlsx",
    "manifest": "storage/processed/239b.../spreadsheet_manifest.json"
  },
  "warnings": [],
  "errors": []
}
```
