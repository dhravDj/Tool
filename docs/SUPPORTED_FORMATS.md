# DocuMind AI — Universal Format Support Matrix

**Platform Version:** 0.4.0  
**Last Updated:** November 6, 2026  

---

## 1. Supported Format Summary by Pipeline

| Pipeline Engine | Purpose | Formats Supported | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Universal File Detection** (Phase 2) | Identification, verification & triage | **45+ formats across 17 categories** | 7-stage arbitration, magic bytes, MIME, safe containers, extension mismatch alerts. |
| **Document Content Extraction** (Phase 3) | Structured text & AST extraction | **PDF, DOCX, DOC, TXT, MD, RTF, ODT, EPUB** | Bounding boxes, reading order, table matrices, zero-macro execution, OCR fallback. |
| **Image & Visual Intelligence** (Phase 4) | Vision understanding & OCR | **PNG, JPEG, JPG, WEBP, TIFF, BMP, SVG** | EXIF sanitization, deskewing, Otsu binarization, tiling, scene captioning, charts, diagrams, VQA. |

---

## 2. Image & Visual Intelligence Formats (Phase 4)

| Format ID | Common Extensions | MIME Type | Container / Signature | Capabilities | Privacy / Safety Safeguards |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `png` | `.png` | `image/png` | `\x89PNG\r\n\x1a\n` | OCR, deskew, binarization, color palette, objects | 89 MP limit, alpha channel extraction |
| `jpeg` | `.jpg`, `.jpeg` | `image/jpeg` | `\xff\xd8\xff` | OCR, EXIF metadata, scene captioning, objects | **Automatic GPS coordinate sanitization** |
| `webp` | `.webp` | `image/webp` | RIFF / `WEBP` | OCR, animation frame count, lossless/lossy mode | Header-only size check, 89 MP limit |
| `tiff` | `.tif`, `.tiff` | `image/tiff` | `II*\x00` / `MM\x00*` | Multi-page OCR, high-resolution document scans | IFD directory bounds, uncompressed buffer caps |
| `bmp` | `.bmp` | `image/bmp` | `BM` | Fast raw bitmap processing, OCR, charts | Decompression bomb bounds check |
| `svg` | `.svg` | `image/svg+xml` | XML `<svg>` | Structural vector analysis, node/text extraction | **`defusedxml` protection (zero XXE / SSRF)** |
| `gif` | `.gif` | `image/gif` | `GIF87a` / `GIF89a` | Frame count, animation duration, palette analysis | Animated frame processing limits |

---

## 3. Document Content Extraction Formats (Phase 3)

| Format ID | Primary Extension | Engine Adapter | Structural Output | Scanned / OCR Support |
| :--- | :--- | :--- | :--- | :--- |
| `pdf` | `.pdf` | `PDFExtractor` (`PyMuPDF`) | Pages, blocks, table grids, headers, reading order | Density check (< 40 chars/page) -> `OCRRouter` |
| `docx` | `.docx` | `DocxExtractor` (`python-docx`) | Headings 1–6, paragraphs, tables, lists, links | Structural XML extraction |
| `doc` | `.doc` | `LegacyDocExtractor` (`olefile` / LibreOffice) | OLE summary metadata, safe text runs | **Zero macro execution (VBA flagged)** |
| `txt` | `.txt` | `PlainTextExtractor` | BOM auto-detection, paragraphs, indentation | UTF-8, CP1252, Latin-1 fallbacks |
| `md` | `.md`, `.markdown` | `MarkdownExtractor` | Frontmatter YAML, H1–H6, code blocks, tables | Native Markdown parsing |
| `rtf` | `.rtf` | `RTFExtractor` (`striprtf`) | Formatted text stripping, paragraphs | Pure Python conversion |
| `odt` | `.odt` | `ODTExtractor` | OpenDocument XML (`content.xml`, `meta.xml`) | Headings, paragraphs, tables, lists |
| `epub` | `.epub` | `EPUBExtractor` (`ebooklib`) | Dublin Core metadata, spine reading order | Multi-chapter HTML extraction |

---

## 4. Universal Detection Catalog (Phase 2 Categories)

1. **Document:** `pdf`, `docx`, `doc`, `rtf`, `odt`, `txt`, `md`
2. **Spreadsheet:** `xlsx`, `xls`, `csv`, `tsv`, `ods`
3. **Presentation:** `pptx`, `ppt`, `odp`
4. **Image:** `png`, `jpeg`, `webp`, `tiff`, `bmp`, `svg`, `gif`, `ico`, `heic`
5. **Audio:** `mp3`, `wav`, `flac`, `aac`, `ogg`, `m4a`
6. **Video:** `mp4`, `mkv`, `avi`, `mov`, `webm`
7. **Archive:** `zip`, `tar`, `gz`, `7z`, `rar`, `bz2`
8. **Code:** `py`, `js`, `ts`, `html`, `css`, `c`, `cpp`, `java`, `go`, `rs`
9. **Structured Data:** `json`, `xml`, `yaml`, `toml`, `sql`, `parquet`
10. **Ebook:** `epub`, `mobi`
11. **Font:** `ttf`, `otf`, `woff`, `woff2`
12. **Executable:** `elf`, `pe_exe`, `macho`, `wasm` (flagged as suspicious when uploaded disguised as document/image)
13. **Email:** `eml`, `msg`
14. **Other Binary:** `sqlite`, `bin`
