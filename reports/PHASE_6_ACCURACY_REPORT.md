# DocuMind AI — Phase 6 Extraction Accuracy Report

**Phase:** Phase 6 — Presentation Intelligence  
**Evaluation Date:** 2026-11-06T06:55:00 UTC  
**Scope:** Ground-truth validation of presentation structures, element positioning, bullet hierarchies, tables, native charts, images, and notes.

---

## 1. Ground Truth Accuracy Matrix

| Format | Tested Fixture | Expected Structure | Extracted Structure | Accuracy | Notes |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **PPTX** | `pptx_basic_text.pptx` | 2 slides, 2 text blocks | 2 slides, 2 text blocks | **100%** | Titles and body text captured exactly |
| **PPTX** | `pptx_nested_bullets.pptx` | Bullets at levels 0, 1, 2 | Bullets at levels 0, 1, 2 | **100%** | Exact indentation depth preserved |
| **PPTX** | `pptx_tables.pptx` | 4 rows × 3 columns, headers | 4 rows × 3 columns, headers | **100%** | Cell coordinates & text match ground truth |
| **PPTX** | `pptx_native_charts.pptx` | Clustered column, 4 cats, 2 series | Clustered column, 4 cats, 2 series | **100%** | Categories, series names & numbers exact |
| **PPTX** | `pptx_images.pptx` | 1 embedded PNG, 300×200 | 1 embedded PNG, SHA256 verified | **100%** | Asset extracted & persisted without corruption |
| **PPTX** | `pptx_speaker_notes.pptx` | "CFO sign-off" note | "CFO sign-off" note | **100%** | Kept segregated from visible slide text |
| **PPTX** | `pptx_grouped_shapes.pptx` | 2 boxes + 1 arrow | 2 shapes + arrow connector | **100%** | Diagram structure identified |
| **PPTX** | `pptx_hidden_slides.pptx` | 3 slides (1 hidden) | 3 slides (`hidden_slide_count=1`) | **100%** | `show="0"` flag correctly parsed |
| **PPTX** | `pptx_unicode_hindi.pptx` | "नमस्ते दुनिया — DocuMind AI" | "नमस्ते दुनिया — DocuMind AI" | **100%** | Multilingual UTF-8 unicode fully preserved |
| **ODP** | `odp_text_tables.odp` | 2 slides, 1 table, 1 note | 2 slides, 1 table, 1 note | **100%** | XML elements parsed natively via `defusedxml` |
| **PPT** | `legacy_powerpoint.ppt` | 1 slide, 2 text blocks | 1 slide, 2 text blocks | **100%** | Native OLE2 stream parser extracted text |
| **PPTX** | `corrupted_presentation.pptx`| Malformed zip container | `is_corrupted=True` | **100%** | Corrupted package caught defensively |

---

## 2. Capability Confidence Metrics

| Extraction Dimension | Confidence Score | Evaluation Criteria |
| :--- | :---: | :--- |
| **Slide Count & Ordering** | **1.00** | Strict 1-to-1 match with presentation slide sequences across PPTX, PPT, and ODP |
| **Bullet Nesting & Levels** | **1.00** | Indentation levels (0, 1, 2) accurately extracted and formatted into Markdown |
| **Table Structural Preservation** | **1.00** | Rows, columns, headers, and text contents verified against table shapes |
| **Chart Data Precision** | **1.00** | Native series values and category strings extracted without floating-point drift |
| **Speaker Notes Isolation** | **1.00** | $0\%$ text leakage into visible slide text; separate speaker notes section in Markdown |
| **Defensive Exception Handling** | **1.00** | Zero unhandled exceptions or crashes on truncated or corrupted fixtures |

---

## 3. Findings & Limitations

- **Chart Data Coverage:** Native charts in PPTX are fully extracted down to numeric series values. Inferred charts (static images representing charts) are cataloged as `is_inferred=True` and routed to the Image Intelligence chart extractor.
- **Legacy PPT Environment Variance:** In environments with LibreOffice installed, legacy PPT presentations undergo full visual conversion to PPTX. When LibreOffice is not installed, the engine uses the native OLE2 compound binary parser, extracting metadata and text records (`TextBytesAtom`, `TextCharsAtom`) with transparent informational warnings.
