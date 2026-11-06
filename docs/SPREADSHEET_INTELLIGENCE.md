# DocuMind AI — Spreadsheet Intelligence Engine Architecture

## 1. Overview & Architectural Goals

The **Spreadsheet Intelligence Engine** in DocuMind AI is a production-grade, modular, and extensible system designed to ingest, parse, profile, structure, and export tabular data from modern and legacy spreadsheet formats.

Unlike simple converters that discard workbook context, DocuMind AI preserves:
- **Workbook Architecture:** Multi-sheet structure, tab order, sheet visibility (visible, hidden, very hidden).
- **Cell Structure & Formatting:** Raw values, formatted display strings, data types, fonts, fills, alignments, borders, number formatting, and merged cell ranges.
- **Formula Intelligence (Non-Executing):** Static AST classification (lookup, math/aggregation, conditional, text, datetime), dependency mapping, and cross-sheet references without executing untrusted code or macros.
- **Data Understanding & Statistical Profiling:** Automated column type inference, null counts, distinct counts, summary statistics (mean, median, standard deviation, min, max), candidate primary key detection, and duplicate row metrics.
- **Security Hardening:** Automatic DDE formula injection sanitization on CSV exports (prepending `'` to `=`, `+`, `-`, `@`, `\t`, `\r`), zero macro execution, ZIP bomb protection, and strict cell bounds.
- **Multi-Format Output Generation:** Deterministic export to canonical JSON, human-readable Markdown reports, sanitized CSV, reconstructed XLSX, and Apache Parquet.

```
                  ┌───────────────────────────────────────────────┐
                  │           Ingested Spreadsheet File           │
                  │        (XLSX / XLS / CSV / TSV / ODS)         │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │       Universal File Detection Engine         │
                  │   MIME, Signature, Extension, Validity Check  │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │        Spreadsheet Intelligence Router        │
                  └───────┬───────────────┬───────────────┬───────┘
                          │               │               │
            ┌─────────────┴──┐     ┌──────┴───────┐ ┌─────┴──────────┐
            │  XLSX Adapter  │     │ Delimited    │ │ ODS Adapter    │
            │  (openpyxl)    │     │ (CSV / TSV)  │ │ (defused XML)  │
            └─────────────┬──┘     └──────┬───────┘ └─────┬──────────┘
                          │               │               │
                          └───────────────┼───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │    Formula & Security Engine  │
                          │ - Passive AST Classification  │
                          │ - Cross-Sheet Ref Mapping     │
                          │ - DDE CSV Injection Sanitizer │
                          │ - Zero Macro Execution        │
                          └───────────────┬───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │   Data Understanding Engine   │
                          │ - Column Type Inference       │
                          │ - Summary Statistics          │
                          │ - Candidate Primary Keys      │
                          │ - Duplicate Row Detection     │
                          └───────────────┬───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │ Canonical SpreadsheetDocument │
                          └───────────────┬───────────────┘
                                          │
        ┌───────────────────┬─────────────┴─────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  JSON Model  │    │   Markdown   │    │  Sanitized   │    │ Reconstructed│
│  (Canonical) │    │  Executive   │    │   RFC CSV    │    │ XLSX / Pq    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 2. Supported Formats & Adapter Implementations

| Format | Extension | Primary Engine | Parsing Technique | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Excel OpenXML** | `.xlsx` | `openpyxl` | XML ZIP Archive | Multi-sheet, formulas, styles, merged ranges, tables, charts, comments, validations |
| **Legacy Excel** | `.xls` | `xlrd` | Binary BIFF8 Record Stream | Legacy 97–2003 workbooks, sheet enumeration, cell formatting, type conversions |
| **Comma-Separated** | `.csv` | Python `csv` | Sniffer + Multi-Encoding Detection | Delimiter sniffing (`,`, `;`, `\t`, `\|`), UTF-8/BOM/Latin-1, multi-line quoted fields |
| **Tab-Separated** | `.tsv` | Python `csv` | Sniffer + Multi-Encoding Detection | High-throughput TSV data grids, ragged row normalization |
| **OpenDocument** | `.ods` | Python XML / Zip | `defusedxml` `content.xml` Stream | Multi-sheet ODF 1.3, XML namespace handling, safe non-resolving entity parsing |

### 2.1 XLSX Adapter (`XLSXAdapter`)
- Leverages `openpyxl` in read-only / formula-preservation mode (`data_only=False` for formula extraction, plus cached value extraction).
- Extracts font properties (family, size, bold, italic, color), fills (pattern type, hex RGB), cell alignments (horizontal, vertical), and borders.
- Preserves merged cell address ranges (e.g., `A1:F1`).
- Identifies embedded Excel Table structures (`TableMetadata`) with header names and total row flags.
- Catalogs embedded Chart objects (`ChartMetadata`) with chart titles, types, and series definitions.

### 2.2 Delimited Adapter (`DelimitedSpreadsheetAdapter`)
- Multi-encoding detection with fallback chain: `utf-8` -> `utf-8-sig` (BOM) -> `latin1` -> `cp1252`.
- Delimiter sniffing across standard and regional delimiters (`,`, `\t`, `;`, `|`).
- Full RFC 4180 compliance with embedded newline support inside double quotes.
- Ragged row normalization ensuring uniform column widths across all rows.

### 2.3 Legacy XLS Adapter (`LegacyXLSAdapter`)
- Uses `xlrd` to decode proprietary Microsoft Excel BIFF8 compound binary files.
- Converts Excel serial date floats (`xldate_as_tuple`) into ISO 8601 timestamps.
- Extracts sheets, dimensions, cell types (text, number, date, boolean, error, blank).

### 2.4 ODS Adapter (`ODSAdapter`)
- Uses standard library `zipfile` and `xml.etree.ElementTree` with `defusedxml` hardening.
- Parses `content.xml` across OASIS OpenDocument namespaces:
  - `urn:oasis:names:tc:opendocument:xmlns:office:1.0`
  - `urn:oasis:names:tc:opendocument:xmlns:table:1.0`
  - `urn:oasis:names:tc:opendocument:xmlns:text:1.0`
- Supports `table:number-rows-repeated` and `table:number-columns-repeated` expansion up to safety ceilings.

---

## 3. Formula Inspection & Dependency Mapping

DocuMind AI implements **passive, non-executing formula intelligence**:

1. **Zero Execution Policy:** Formulas are parsed into AST tokens and regex patterns. Formulas are **never** evaluated through Python `eval()`, JavaScript runtimes, or external spreadsheet execution environments.
2. **Formula Categorization:**
   - `math_aggregation`: `SUM`, `AVERAGE`, `MIN`, `MAX`, `COUNT`, `ROUND`, `PRODUCT`, etc.
   - `conditional`: `IF`, `SUMIF`, `COUNTIF`, `IFERROR`, `AND`, `OR`, `NOT`.
   - `lookup`: `VLOOKUP`, `HLOOKUP`, `XLOOKUP`, `INDEX`, `MATCH`, `LOOKUP`, `CHOOSE`.
   - `text`: `CONCAT`, `CONCATENATE`, `TEXT`, `LEFT`, `RIGHT`, `MID`, `TRIM`, `LEN`.
   - `datetime`: `DATE`, `TIME`, `NOW`, `TODAY`, `YEAR`, `MONTH`, `DAY`.
   - `arithmetic`: Standard operator expressions (`+`, `-`, `*`, `/`, `^`).
3. **Cross-Sheet Reference Tracking:**
   - Detects references matching `SheetName!A1` or `'Quoted Sheet'!$B$10:$C$20`.
   - Enables graph dependency analysis across multiple tabs.
4. **External Reference Isolation:**
   - Identifies references pointing to external files (e.g., `[Budget2025.xlsx]Sheet1!A1`).
   - Flags them as external without dereferencing or fetching external files over network or local storage.

---

## 4. Data Understanding & Statistical Profiling

For each worksheet, the `DataUnderstandingProfiler` computes:

- **Type Inference:** Analyzes populated values to categorize each column as `integer`, `float`, `boolean`, `date`, `currency`, `percentage`, or `text`.
- **Completeness & Null Counts:** Number of populated vs. missing cells.
- **Cardinality & Uniqueness:** Number of distinct values and frequent value distributions.
- **Candidate Primary Key Detection:** Columns with $100\%$ populated cells and $100\%$ unique values are automatically tagged as candidate primary keys (`is_candidate_key=True`).
- **Summary Statistics:** Computes `mean`, `median`, `std_dev`, `min_value`, and `max_value` for numeric and financial columns.
- **Duplicate Rows:** Counts exact duplicate row patterns across all non-empty columns.

---

## 5. Security & Threat Modeling

| Threat Vector | Mitigation Strategy | Enforcement |
| :--- | :--- | :--- |
| **CSV Formula Injection (DDE)** | Exported strings beginning with `=`, `+`, `-`, `@`, `\t`, `\r` are prefixed with `'` (single quote). | `FormulaInspector.sanitize_for_csv_export()` |
| **VBA Macro / Code Execution** | Macros in `.xlsm` or `.xls` are stripped and completely ignored. | Default adapter behavior |
| **ZIP Decompression Bombs** | Strict XML size caps (100MB maximum expanded size) and cell ceilings (1,000,000 cells max). | Adapter bounds check |
| **XXE in XML / ODS / XLSX** | Entity resolution is disabled during XML parsing (`defusedxml`). | ODS & XML parsing routines |
| **External Network SSRF** | Formulas referencing external URLs (`HYPERLINK`, `WEBSERVICE`) are stored as text strings only. | Zero network dispatch |
| **Directory Traversal** | Storage keys and artifact outputs are resolved via hardened local storage paths. | `local_storage._resolve_safe_path` |

---

## 6. Output Generators

The pipeline provides 6 output formats:
1. **Canonical JSON (`SpreadsheetJSONGenerator`):** Full, loss-less serialization of the `SpreadsheetDocument` model.
2. **Executive Markdown (`SpreadsheetMarkdownGenerator`):** Formatted tables, workbook properties, formula counts, and data profiling summaries.
3. **Sanitized CSV (`SpreadsheetCSVExporter`):** RFC 4180 CSV export with DDE injection sanitization for any worksheet.
4. **Excel Reconstruction (`SpreadsheetXLSXExporter`):** Builds a clean multi-sheet `.xlsx` file preserving merged ranges and formulas.
5. **Apache Parquet (`SpreadsheetParquetExporter`):** High-efficiency columnar storage for downstream analytics (enabled when `pyarrow` is available).
6. **Execution Manifest (`SpreadsheetManifestGenerator`):** Audit manifest recording runtimes, cell counts, and generated artifact references.
