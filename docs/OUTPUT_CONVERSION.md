# Output Conversion Specification

DocuMind transforms normalized `UniversalContent` into clean, compliant, and secure output formats.

---

## 1. Supported Target Formats

### TXT (Plain Text — Mode A)
- **Encoding**: UTF-8 without BOM.
- **Line Breaks**: Clean UNIX (`\n`) newlines.
- **Formatting**: Strips markdown markup, table borders, and HTML tags. Preserves meaningful paragraph breaks, section headings, and transcript speech lines with timestamps (`[01:23] Speaker 1: Hello`).

### Markdown (Structured Text — Mode B)
- **Standard**: GitHub Flavored Markdown (GFM).
- **Frontmatter**: YAML frontmatter containing `title`, `author`, `source_file`, `source_format`, and `page_count`.
- **Headings**: Normalized hierarchical headers (`#`, `##`, `###`).
- **Tables**: Clean GFM markdown tables with aligned pipes (`|`) and hyphens (`---`).
- **Code**: Fenced with triple backticks and language identifiers (` ```python `).
- **Boundaries**: Page, slide, and worksheet boundaries preserved as structured section headings or HTML comments.

### JSON (Structured Data)
- **Standard**: JSON Schema compliant with `version: "2.0.0"`.
- **Structure**:
  ```json
  {
    "version": "2.0.0",
    "document": {
      "source_filename": "sample.pdf",
      "source_format": "pdf",
      "title": "Document Title",
      "author": "Author",
      "page_count": 5,
      "word_count": 1200,
      "metadata": {},
      "warnings": []
    },
    "content": {
      "sections": [],
      "paragraphs": [],
      "tables": [],
      "code_blocks": [],
      "transcript_segments": [],
      "raw_text_length": 6500
    }
  }
  ```

### CSV (Tabular Export)
- **Quoting**: `csv.QUOTE_MINIMAL` with standard comma delimiters and RFC 4180 escaping.
- **Formula Injection (DDE) Sanitization**:
  Spreadsheet applications (Excel, Calc) execute formulas if a cell starts with `=`, `+`, `-`, `@`, `\t`, or `\r`.
  
  **Safe Formula Neutralization Rule**:
  - If a cell starts with `=`, `@`, `\t`, or `\r`, prepend a single quote (`'`).
  - If a cell starts with `+` or `-`:
    - Check if it represents a valid numeric literal (e.g., `-42.5`, `-100`, `+2500`, `-1.5e-3`).
    - If it **is a valid number**, keep it untouched. **Legitimate negative numbers are never corrupted**.
    - If it **is not a valid number** (e.g., `-2+3*cmd|' /C calc'!A0`), prepend a single quote (`'`).

### HTML (Semantic Document)
- **Responsive Layout**: Clean standalone HTML5 document with CSS variables for light and dark modes.
- **Security**: Complete character escaping via `html.escape(..., quote=True)` on all extracted text, table values, headings, and code snippets.
- **Script Execution**: Zero `<script>` tags, inline event handlers (`onload`, `onerror`), or `javascript:` URLs are emitted or executed.

### ZIP (Complete Extraction Bundle — Mode C)
- **Compression**: Standard Deflated ZIP container.
- **Artifacts**:
  - `document.txt`: Mode A plain text.
  - `document.md`: Mode B structured Markdown.
  - `document.json`: Full structured JSON AST.
  - `document.html`: Standalone rendered HTML document.
  - `metadata.json`: Extracted file metadata.
  - `manifest.json`: Verification manifest detailing file counts, sizes, and timestamps.
  - `tables/*.csv`: Every table exported as a sanitized CSV.
  - `subtitles/*.srt`, `*.vtt`: Timed speech subtitle tracks for audio and video media.
