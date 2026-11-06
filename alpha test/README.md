# DocuMind AI — Alpha Test Dataset

This is a synthetic, license-safe starter dataset for manual alpha testing. It contains 130 files across supported-format samples and negative fixtures.

## Folder guide
- `01_pdf/` — 30 generated PDFs with known text tokens and simple tables.
- `02_doc_docx/` — 18 valid DOCX files and 2 deliberately mislabeled `.doc` negative fixtures. The `.doc` files are NOT genuine legacy binary DOC documents.
- `03_other_documents/` — TXT, Markdown, RTF, ODT and EPUB fixtures.
- `04_images/` — raster and SVG image fixtures with visible OCR tokens.
- `05_spreadsheets/` — XLSX workbooks with multiple sheets, formulas, hidden sheets, charts and validation; CSV/TSV edge cases.
- `06_corrupted_unsupported/` — malformed, truncated, unknown and mismatched files.
- `reports/` — use this folder for manual test results.

## Important
1. All files are synthetic. Do not treat this dataset as a full accuracy benchmark.
2. OCR fixtures use high-contrast printed text; they do not represent handwriting or difficult real-world scans.
3. PDF files are digitally generated, not scanned PDFs.
4. Spreadsheet formulas are included as formula text. A parser may expose cached values differently depending on the engine; do not assume recalculation.
5. The two `.doc` fixtures are intentionally invalid/mislabeled and should not be used to claim successful legacy DOC extraction.
6. Some advanced features (e.g. pivot tables, macros, complex charts, embedded OLE objects) are not represented.
7. Run suspicious/corrupted fixtures only in an isolated test environment.
8. Never upload private or sensitive documents to an external AI provider without explicit consent.

## Ground truth
`manifest.json` contains each file's relative path, SHA-256, expected classification and key validation tokens/features.

## Suggested workflow
Upload a file → detect format → run the relevant extraction/analysis → compare output against manifest → record pass/fail and notes in `reports/ALPHA_MANUAL_RESULTS.csv`.

## Suggested manual result columns
test_id,file,expected_result,actual_result,status,issue_id,notes,processing_ms,peak_memory_mb
