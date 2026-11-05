# DocuMind AI — Supported Document Formats (Phase 3)

This document provides a comprehensive operational reference for the eight core document formats supported for extraction in Phase 3.

## 1. Portable Document Format (PDF)
- **Format ID**: `pdf`
- **MIME Types**: `application/pdf`
- **Extensions**: `.pdf`
- **Detection**: Magic bytes `%PDF-`, libmagic, PDF version header parser.
- **Engine**: `pymupdf_extractor` (`PyMuPDF` / `fitz`)
- **Extracted Content**:
  - Text blocks with exact floating-point bounding boxes `[x0, y0, x1, y1]`.
  - Native table detection via `page.find_tables()`. Table grids formatted as Markdown tables.
  - Page rotation, width, and height in standard typographic points (72 DPI).
  - PDF document information dictionary (Author, Title, Subject, Creator, Dates).
  - Encrypted / password-protected document detection (`doc.is_encrypted`). Rejects unauthorized extraction with `PasswordRequiredError`.
  - Scanned page detection (< 40 digital characters with embedded images) with routing to `OCRRouter`.

## 2. Microsoft Word Modern (DOCX)
- **Format ID**: `docx`
- **MIME Types**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Extensions**: `.docx`, `.dotx`
- **Detection**: ZIP container verification containing `word/document.xml`.
- **Engine**: `docx_extractor` (`python-docx`)
- **Extracted Content**:
  - Headings (levels 1 through 6) based on style descriptors.
  - Body paragraphs in sequential reading order.
  - Bulleted and numbered list items.
  - Full table grids with cell coordinates.
  - Section headers and footers.
  - Hyperlinks extracted from relationship references.
  - Dublin Core properties (`core_properties`: Title, Author, Subject, Revision, Dates).

## 3. Microsoft Word Legacy Binary (DOC)
- **Format ID**: `doc`
- **MIME Types**: `application/msword`
- **Extensions**: `.doc`, `.dot`
- **Detection**: OLE2 compound document signature (`\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1`).
- **Engine**: `legacy_doc_extractor` (`olefile` stream extraction)
- **Security Safeguard**: Zero macro execution. VBA/macro streams are audited and flagged as security warnings.
- **Extracted Content**:
  - Summary information streams (`\x05SummaryInformation`, `\x05DocumentSummaryInformation`).
  - Text runs extracted from the binary `WordDocument` stream (UTF-16LE and ASCII runs).
  - Paragraph segmentation and heading heuristics.

## 4. Plain Text (TXT)
- **Format ID**: `txt`
- **MIME Types**: `text/plain`
- **Extensions**: `.txt`, `.text`
- **Detection**: Printable ASCII/UTF-8 ratio, absence of binary control characters.
- **Engine**: `plain_text_extractor` (Native Python)
- **Extracted Content**:
  - Encoding auto-detection with BOM detection (UTF-8 BOM, UTF-16 LE/BE, UTF-32 LE/BE).
  - Fallback sequence: UTF-8 -> Windows-1252 / CP1252 -> ISO-8859-1 (Latin-1).
  - Paragraph boundaries identified by double newlines, preserving indentation and intra-paragraph line breaks.
  - Word, character, and line count metrics.

## 5. Markdown (MD)
- **Format ID**: `md`
- **MIME Types**: `text/markdown`, `text/x-markdown`
- **Extensions**: `.md`, `.markdown`
- **Detection**: Markdown structural tokens (`# `, `## `, fenced code blocks, table pipes).
- **Engine**: `markdown_extractor` (Native Python + PyYAML)
- **Extracted Content**:
  - YAML frontmatter parsed into document metadata.
  - Headings 1 through 6 with level preservation.
  - Fenced code blocks with language identifiers.
  - Markdown table syntax parsed into 2D table grids.
  - List items with bullet / numerical classification.

## 6. Rich Text Format (RTF)
- **Format ID**: `rtf`
- **MIME Types**: `application/rtf`, `text/rtf`
- **Extensions**: `.rtf`
- **Detection**: Magic byte signature `{\rtf`.
- **Engine**: `rtf_extractor` (`striprtf`)
- **Extracted Content**:
  - Stripped clean text free of RTF control tags and fonts.
  - Paragraph and heading division.
  - Document word and character counts.

## 7. OpenDocument Text (ODT)
- **Format ID**: `odt`
- **MIME Types**: `application/vnd.oasis.opendocument.text`
- **Extensions**: `.odt`
- **Detection**: ZIP container verification containing `mimetype` with `opendocument.text` and `content.xml`.
- **Engine**: `odt_extractor` (`xml.etree.ElementTree` / `zipfile`)
- **Extracted Content**:
  - XML elements: `text:h` (headings with outline levels), `text:p` (paragraphs), `text:list` (lists).
  - Tabular data: `table:table`, `table:table-row`, `table:table-cell`.
  - Document metadata from `meta.xml` (title, author, creation date, description).

## 8. Electronic Publication (EPUB)
- **Format ID**: `epub`
- **MIME Types**: `application/epub+zip`
- **Extensions**: `.epub`
- **Detection**: ZIP container verification containing `META-INF/container.xml`.
- **Engine**: `epub_extractor` (`ebooklib` + `BeautifulSoup4`)
- **Extracted Content**:
  - Dublin Core publication metadata (title, author, language, publisher, identifier).
  - Spine reading order preservation across multi-part chapters.
  - HTML element parsing: `h1`..`h6` headings, `p` paragraphs, `li` list items, `table` grids.
  - Image reference extraction and asset export.
