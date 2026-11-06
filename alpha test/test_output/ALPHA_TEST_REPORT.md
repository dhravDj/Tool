# DocuMind AI — Alpha Test Suite Verification Report

**Test Date:** 2026-11-06 06:24:34 UTC  
**Dataset Location:** `alpha test/`  
**Output Directory:** `alpha test/test_output/`  
**Overall Verdict:** **PASSED (100%)**  

---

## 1. Executive Summary

- **Total Fixtures Evaluated:** 130
- **Passed:** **130 / 130** (100.0%)
- **Failed:** 0
- **Total Processing Duration:** 8.50 seconds
- **Average Duration Per Fixture:** 65.38 ms
- **Peak Resident Set Size:** 569.96 MB

---

## 2. Category Performance & Pass Rates

| Category | Fixtures | Passed | Failed | Pass Rate | Avg Latency | Latency Range |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PDF** | 30 | 30 | 0 | **100.0%** | 262.05 ms | 196.5 ms – 670.9 ms |
| **DOCX** | 18 | 18 | 0 | **100.0%** | 14.04 ms | 12.1 ms – 28.4 ms |
| **NEGATIVE_DOC** | 2 | 2 | 0 | **100.0%** | 4.95 ms | 3.2 ms – 6.7 ms |
| **TXT** | 5 | 5 | 0 | **100.0%** | 3.30 ms | 2.9 ms – 3.6 ms |
| **MD** | 3 | 3 | 0 | **100.0%** | 3.52 ms | 3.4 ms – 3.7 ms |
| **RTF** | 2 | 2 | 0 | **100.0%** | 3.12 ms | 3.1 ms – 3.2 ms |
| **ODT** | 2 | 2 | 0 | **100.0%** | 1.44 ms | 1.3 ms – 1.6 ms |
| **EPUB** | 3 | 3 | 0 | **100.0%** | 6.22 ms | 2.1 ms – 14.0 ms |
| **PNG** | 6 | 6 | 0 | **100.0%** | 1.13 ms | 0.6 ms – 3.7 ms |
| **JPEG** | 6 | 6 | 0 | **100.0%** | 0.86 ms | 0.7 ms – 1.6 ms |
| **WEBP** | 6 | 6 | 0 | **100.0%** | 1.86 ms | 1.3 ms – 4.6 ms |
| **TIFF** | 5 | 5 | 0 | **100.0%** | 3.08 ms | 2.2 ms – 5.9 ms |
| **BMP** | 5 | 5 | 0 | **100.0%** | 3.14 ms | 2.9 ms – 3.9 ms |
| **SVG** | 2 | 2 | 0 | **100.0%** | 1.32 ms | 1.2 ms – 1.4 ms |
| **XLSX** | 12 | 12 | 0 | **100.0%** | 16.47 ms | 11.3 ms – 66.3 ms |
| **CSV** | 6 | 6 | 0 | **100.0%** | 1.38 ms | 0.7 ms – 4.2 ms |
| **TSV** | 2 | 2 | 0 | **100.0%** | 7.19 ms | 3.4 ms – 11.0 ms |
| **CORRUPTED_OR_UNSUPPORTED** | 15 | 15 | 0 | **100.0%** | 1.92 ms | 0.0 ms – 8.2 ms |

---

## 3. Detailed Category Verifications

### 3.1 PDF Documents (`01_pdf/`)
- **Fixtures:** 30 PDF files.
- **Verifications:** Format detection, page count verification, reading order extraction, table detection, and text recall of end tokens (`ALPHA-001-END` to `ALPHA-030-END`).
- **Result:** **100% Pass** across all 30 documents.

### 3.2 Microsoft Word (`02_doc_docx/`)
- **Fixtures:** 18 DOCX files + 2 deliberately mislabeled `.doc` negative fixtures.
- **Verifications:** DOCX token extraction, table parsing, list/bullet counting; for `.doc`, detected as text format and flagged with `is_mismatch=True`.
- **Result:** **100% Pass** across all 20 fixtures.

### 3.3 Other Text & eBook Documents (`03_other_documents/`)
- **Fixtures:** 15 files spanning TXT (5), MD (3), RTF (2), ODT (2), and EPUB (3).
- **Verifications:** Multi-language UTF-8 unicode encoding (`नमस्ते दुनिया — café — 東京`), Markdown tables, RTF formatting, OpenDocument text, and EPUB chapter flows.
- **Result:** **100% Pass** across all 15 files.

### 3.4 Image & Visual Formats (`04_images/`)
- **Fixtures:** 30 files spanning PNG (6), JPEG (6), WEBP (6), TIFF (5), BMP (5), and SVG (2).
- **Verifications:** Header detection, dimensions integrity ([900, 600]), XML vector parsing for SVG tokens, non-destructive structure verification.
- **Result:** **100% Pass** across all 30 files.

### 3.5 Spreadsheets & Tabular Data (`05_spreadsheets/`)
- **Fixtures:** 20 files spanning XLSX (12), CSV (6), and TSV (2).
- **Verifications:** Multi-sheet extraction (`Sales`, `Summary`, `HiddenData`), non-executing formula address cataloging (`E2`, `E3`, `E4`, `E5`, `B2`), chart detection, delimiter sniffing, and token extraction.
- **Result:** **100% Pass** across all 20 files.

### 3.6 Corrupted, Truncated & Unsupported Negative Fixtures (`06_corrupted_unsupported/`)
- **Fixtures:** 15 edge cases (truncated PDF, broken XLSX, empty DOCX, bad ZIP, fake images, PE executable disguise, extension mismatches).
- **Verifications:** Robust defensive detection without runtime crashes; verified `is_corrupted`, `is_mismatch`, `is_valid=False`, or `warnings` indicators.
- **Result:** **100% Pass** (15/15 edge cases safely handled and isolated).

---

## 4. Output Artifacts Generated

- **CSV Results Ledger:** `alpha test/test_output/alpha_test_results.csv`
- **JSON Results Manifest:** `alpha test/test_output/alpha_test_summary.json`
- **Synchronized Manual Ledger:** `alpha test/reports/ALPHA_MANUAL_RESULTS.csv`
- **Markdown Verification Report:** `alpha test/test_output/ALPHA_TEST_REPORT.md`
