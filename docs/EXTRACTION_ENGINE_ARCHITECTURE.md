# DocuMind AI — Extraction Engine Architecture

## Architectural Principles

1. **Strict Provenance & Zero Hallucination**:
   DocuMind AI Phase 3 is exclusively focused on content and structure extraction. The system never summarizes, fabricates, or interprets text. Extracted blocks retain their raw characters, reading order indices, and source provenance (`native`, `native_table`, `ocr`, `native_header`, `native_footer`).

2. **Security & Sandbox Isolation**:
   - **Zero Code Execution**: Macros and scripts (e.g. Word VBA, Excel macros) are never executed. In legacy `.doc` files, VBA/Macro streams are audited and reported as security warnings without execution.
   - **Resource Limits**: Every adapter enforces page limits (`MAX_EXTRACTION_PAGE_LIMIT = 1000`) and extraction timeouts (`EXTRACTION_TIMEOUT_SECONDS = 300`) to prevent denial-of-service via compression bombs or malformed recursion.
   - **Path Traversal & Archive Defense**: Extracted files and container inspection use secure sanitization without allowing relative parent traversals (`..`).

3. **Extensibility via Dependency Inversion**:
   All extractors inherit from `BaseDocumentExtractor`, implementing the `ExtractionEngineInterface` and `ProcessingPluginInterface`. Any new engine (e.g. Docling, MinerU, custom cloud parser) can be plugged in by registering it with `extraction_pipeline.register_extractor()` without modifying upstream controllers or routes.

---

## OCR Subsystem & Hybrid Routing

DocuMind AI provides an intelligent page-level OCR router (`OCRRouter`):
- For digital PDFs, text blocks and bounding boxes are extracted directly from PDF font dictionaries at sub-millisecond speeds.
- For pages with low digital text density (< 40 characters) and present raster images, the page is classified as `is_scanned = True`.
- When OCR is enabled (`OCR_ENABLED=True`) and an OCR engine (such as `TesseractOCRAdapter`) is available, the page is rendered to a 200 DPI bitmap and OCR is executed asynchronously in a dedicated worker thread via `asyncio.to_thread`.
- Word-level confidence scores are calculated and averaged per block.
- Text blocks within extracted tables are de-duplicated against raw text bounding boxes to eliminate redundant paragraphs.

---

## Storage & Artifact Partitioning

Every extraction job writes artifacts to:
`storage/processed/{file_id}/`
- `canonical_document.json`: The complete structured AST containing pages, blocks, bounding boxes, confidence, and metadata.
- `document.md`: GitHub Flavored Markdown generated deterministically from the canonical blocks.
- `manifest.json`: Execution manifest recording timestamps, duration, overall confidence, warning lists, and generated file maps.
- `assets/`: Embedded images extracted from the document.
