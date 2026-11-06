# DocuMind AI — Presentation Intelligence Engine Architecture

## 1. Overview & Architectural Goals

The **Presentation Intelligence Engine** in DocuMind AI is a production-grade, modular, and extensible system designed to ingest, parse, structure, and export rich presentation content from modern and legacy slide formats.

Unlike simple text dumpers that discard layout and slide context, DocuMind AI preserves:
- **Presentation Architecture:** Slide sequencing, dimensions (width, height, aspect ratio 16:9 / 4:3), layout designations, and hidden slide status (`show="0"`).
- **Hierarchical Text & Bullet Nesting:** Paragraph hierarchy with explicit bullet nesting levels (0..N), character runs with styling (bold, italic, underline, font name, font size, colors), and reading order sorting.
- **Tabular Data Structures:** Multi-row, multi-column tables with headers, formatted cells, and coordinate positioning.
- **Native & Inferred Charts:** Extraction of chart types (column, bar, line, pie, doughnut, area, scatter, radar), categories, data series, numeric values, axis titles, and legends, with fallback to Image Intelligence when charts are image-based.
- **Embedded Visual Assets:** Preservation of embedded pictures, image dimensions, SHA256 deduplication, and integration with the Phase 4 Image Intelligence Engine.
- **Diagrams & Flowcharts:** Semantic reconstruction of connected nodes, edges, connectors, arrows, and grouped shapes.
- **Speaker Notes Isolation:** Complete extraction of speaker notes associated with each slide while keeping notes distinctly segregated from visible slide content.
- **Multi-Format Output Generation:** Deterministic export to canonical JSON, human-readable structured Markdown reports, clean plain text streams, and execution manifests.

```
                  ┌───────────────────────────────────────────────┐
                  │          Ingested Presentation File           │
                  │               (PPTX / PPT / ODP)              │
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
                  │       Presentation Intelligence Router        │
                  └───────┬───────────────┬───────────────┬───────┘
                          │               │               │
            ┌─────────────┴──┐     ┌──────┴───────┐ ┌─────┴──────────┐
            │  PPTX Adapter  │     │ Legacy PPT   │ │ ODP Adapter    │
            │ (python-pptx)  │     │(OLE2 / Sandb)│ │ (defused XML)  │
            └─────────────┬──┘     └──────┬───────┘ └─────┬──────────┘
                          │               │               │
                          └───────────────┼───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │    Chart & Diagram Extractor  │
                          │ - Native Series & Categories  │
                          │ - Node-Edge Connectors/Shapes │
                          │ - Group Shape Recursion       │
                          │ - Speaker Notes Extraction    │
                          └───────────────┬───────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │ Canonical PresentationDocument│
                          └───────────────┬───────────────┘
                                          │
        ┌───────────────────┬─────────────┴─────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  JSON Model  │    │   Markdown   │    │  Plain Text  │    │  Execution   │
│ (Canonical)  │    │  Executive   │    │    Stream    │    │   Manifest   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 2. Supported Formats & Adapter Implementations

| Format | Extension | Primary Engine | Parsing Technique | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **PowerPoint OpenXML** | `.pptx` | `python-pptx` | XML ZIP Archive | Multi-slide, bullet hierarchies, tables, native charts, images, speaker notes, grouped shapes, connectors, hidden slides |
| **Legacy PowerPoint** | `.ppt` | `olefile` / LibreOffice | Binary OLE2 / Headless Sandboxed | OLE2 SummaryInformation, binary record stream parsing (TextBytesAtom, TextCharsAtom), slide enumeration, sandboxed headless conversion |
| **OpenDocument Presentation**| `.odp` | `defusedxml` | XML ZIP Archive (`content.xml`) | Standard ODF 1.3 presentation elements, draw:page slides, text:list hierarchy, table:table grids, speaker notes |

---

## 3. Detailed Component Architecture

### 3.1 PPTX Adapter (`PPTXPresentationAdapter`)
- **Package Security Inspection:** Validates ZIP archives before full loading, enforcing caps on total entries (`10,000`), maximum decompressed size (`500 MB`), and high-compression ratio warnings (zip bomb heuristic).
- **Core Presentation Metadata:** Extracts title, subject, author, created/modified dates, slide count, aspect ratio, and layout names.
- **Slide Traversal:** Reads all slides up to `max_slides` (default: 500), inspecting `show="0"` for hidden slide tracking.
- **Paragraphs & Bullet Levels:** Preserves `paragraph.level` (0-indexed indentation) and individual character runs with formatting attributes (font size, bold, italic, underline, color).
- **Native Tables:** Preserves rows, columns, headers, and text cells with coordinate geometry.
- **Native Charts:** Uses `PresentationChartExtractor` to extract chart categories, series names, numeric values, and legend titles across column, bar, line, pie, doughnut, area, scatter, and radar charts.
- **Embedded Media:** Extracts picture blobs, computes SHA256 checksums, and registers assets in `local_storage`.
- **Speaker Notes:** Distinguishes notes from slide body text via `slide.notes_slide.notes_text_frame`.
- **Diagrams & Grouped Shapes:** Detects connector lines and arrows (`PresentationDiagramExtractor`), mapping connected node relationships and grouped sub-elements.

### 3.2 ODP Adapter (`ODPPresentationAdapter`)
- **Secure XML Handling:** Employs `defusedxml.ElementTree` to parse `content.xml` and `meta.xml`, preventing external XML entity (XXE) attacks or entity expansion memory exhaustion.
- **Slide Parsing:** Maps `<draw:page>` elements to slides, resolving layout dimensions in inches from `svg:width` and `svg:height`.
- **Hierarchical Lists:** Recursively parses `<text:list>` and `<text:list-item>` structures into bullet levels.
- **Embedded Tables & Images:** Maps `<table:table>` rows and columns, and reads image files directly from `Pictures/` inside the ODP ZIP container.
- **Speaker Notes:** Parses `<presentation:notes>` blocks attached to each slide.

### 3.3 Legacy PPT Adapter (`PPTPresentationAdapter`)
- **Dual-Tier Strategy:**
  1. **Tier 1 (Headless LibreOffice Sandbox):** If LibreOffice (`soffice`) is installed, converts the `.ppt` file to `.pptx` in an isolated temporary directory with a strict 20-second timeout, zero macro execution, and no network access.
  2. **Tier 2 (Native OLE2 Binary Parser):** If LibreOffice is absent or conversion fails, uses `olefile` to parse OLE2 streams:
     - `\x05SummaryInformation` for title, author, and dates.
     - `PowerPoint Document` stream to unpack binary record atom headers (`0x0FA0` TextCharsAtom, `0x0FA8` TextBytesAtom, `0x0FBA` CString).
     - Returns a structured `PresentationDocument` with transparent conversion warnings.

---

## 4. Security & Resource Controls

1. **Zero Macro Execution:** Macro execution is strictly forbidden and disabled across all presentation parsers.
2. **Defensive Archive Bounds:** ZIP archive entries capped at 10,000 files and 500 MB uncompressed.
3. **Path Traversal Shield:** ZIP entry filenames containing `..` or leading `/` are quarantined.
4. **Execution Timeouts:** Asynchronous extraction operations enforce timeouts to prevent hanging on malformed files.
5. **Memory Protection:** Large image assets are processed incrementally with streaming bytes and stored via content-addressed SHA256 deduplication.
