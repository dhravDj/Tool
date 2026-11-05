# DocuMind AI — Extraction Output Schema Reference

## Schema Hierarchy

```
CanonicalDocument
├── metadata: dict[str, Any]
├── pages: list[CanonicalPage]
│   ├── width: float (points)
│   ├── height: float (points)
│   ├── rotation: int (0, 90, 180, 270)
│   ├── is_scanned: bool
│   ├── ocr_applied: bool
│   └── blocks: list[CanonicalBlock]
└── blocks: list[CanonicalBlock] (flattened sequence in natural reading order)
    ├── block_id: str
    ├── block_type: BlockType
    ├── text: str
    ├── reading_order: int
    ├── page_number: int
    ├── bounding_box: [x0, y0, x1, y1] | null
    ├── confidence: float (0.0 to 1.0) | null
    ├── extraction_engine: str
    ├── provenance: str ("native" | "ocr" | "native_table" | "native_header" | "native_footer")
    ├── warnings: list[str]
    └── metadata: dict[str, Any]
```

---

## Block Types (`BlockType`)

| Enum Value | Name | Description | Example Metadata |
|---|---|---|---|
| `heading` | Heading | Section header | `{"heading_level": 1}` |
| `paragraph` | Paragraph | Standard running prose block | `{"lines": 3}` |
| `list_item` | List Item | Bulleted or numbered item | `{"list_type": "bullet", "marker": "-"}` |
| `table` | Table | Tabular grid of data | `{"table_grid": [["A", "B"], ["1", "2"]], "row_count": 2}` |
| `code` | Code Block | Preformatted source code | `{"language": "python"}` |
| `header` | Header | Top running section header | `{"section_index": 0}` |
| `footer` | Footer | Bottom running page footer | `{"section_index": 0}` |
| `image_reference` | Image Reference | Embedded illustration / photo | `{"image_file": "page_1_img_1.png", "xref": 42}` |

---

## Canonical JSON Example

```json
{
  "document_id": "84c8a2b3-5573-4561-9c02-e01d14870d0b",
  "original_filename": "annual_report.pdf",
  "detected_format": "pdf",
  "extraction_status": "completed",
  "metadata": {
    "title": "Annual Performance Report",
    "author": "Financial Advisory Group",
    "page_count": 1
  },
  "page_count": 1,
  "extraction_engine": "pymupdf_extractor",
  "extraction_version": "2.1.0",
  "created_at": "2026-11-06T03:00:00Z",
  "pages": [
    {
      "page_number": 1,
      "width": 612.0,
      "height": 792.0,
      "rotation": 0,
      "is_scanned": false,
      "ocr_applied": false,
      "blocks": [
        {
          "block_id": "p1_b0_8f43a912",
          "block_type": "heading",
          "text": "Executive Summary",
          "reading_order": 0,
          "page_number": 1,
          "bounding_box": [72.0, 72.0, 340.0, 94.0],
          "confidence": 1.0,
          "extraction_engine": "pymupdf_extractor",
          "provenance": "native",
          "warnings": [],
          "metadata": {
            "type_code": 0
          }
        }
      ]
    }
  ]
}
```

---

## Extraction Manifest Example (`manifest.json`)

```json
{
  "document_id": "84c8a2b3-5573-4561-9c02-e01d14870d0b",
  "original_filename": "annual_report.pdf",
  "detected_format": "pdf",
  "extraction_engine": "pymupdf_extractor",
  "extraction_version": "2.1.0",
  "processing_timestamp": "2026-11-06T03:00:01Z",
  "execution_time_seconds": 0.048,
  "page_count": 1,
  "extracted_block_count": 14,
  "scanned_page_count": 0,
  "ocr_page_count": 0,
  "ocr_engine": null,
  "overall_confidence": 1.0,
  "warnings": [],
  "errors": [],
  "output_files": {
    "canonical_json": "processed/84c8a2b3-5573-4561-9c02-e01d14870d0b/canonical_document.json",
    "markdown": "processed/84c8a2b3-5573-4561-9c02-e01d14870d0b/document.md",
    "manifest": "processed/84c8a2b3-5573-4561-9c02-e01d14870d0b/manifest.json"
  },
  "assets": []
}
```
