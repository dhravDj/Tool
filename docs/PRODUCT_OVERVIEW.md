# DocuMind — Universal File Converter & Content Extractor

## 1. Product Vision & Mission

**DocuMind** is a specialized, production-grade **Universal File Converter and Content Extraction Tool**.

The product has one unambiguous, focused purpose:

> **Take files in any format, extract their authentic content, and convert that content into useful output formats such as TXT, Markdown, JSON, CSV, HTML, and ZIP.**

DocuMind is **NOT** an AI chatbot, RAG platform, or document question-answering tool. All generative conversational interfaces, vector databases, and document Q&A bloat have been decoupled to prioritize what users genuinely need: **fast, accurate, reliable, and secure content extraction and format conversion**.

---

## 2. Core User Workflow

```
┌─────────────────┐
│  UPLOAD FILES   │  Drag-and-drop or batch upload (documents, media, archives, code)
└────────┬────────┘
         │
         ▼
┌───────────────────────────┐
│ AUTOMATIC FORMAT DETECTION│  Multi-signal analysis (Magic bytes, container, MIME, extension)
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│  SELECT EXTRACTION ENGINE │  Routes to format-specific AST / native parser / OCR / speech engine
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│  EXTRACT ORIGINAL CONTENT │  Authentic extraction preserving text, tables, headers, timestamps
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ NORMALIZE CONTENT MODEL   │  Standardized UniversalContent intermediate representation
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ CONVERT INTO TARGET FORMAT│  TXT, Markdown, JSON, CSV, HTML, SRT, VTT, or Complete Bundle
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│   PREVIEW AND DOWNLOAD    │  Instant browser preview, warning report, and direct file download
└───────────────────────────┘
```

---

## 3. The Three Extraction Modes

DocuMind offers three intuitive user-facing extraction modes designed for diverse downstream consumer needs:

### Mode A: Plain Text (`.txt`)
- **Intent**: Extract pure, readable human text without formatting characters.
- **Ideal For**: Ingestion into search indexers, large language models, NLP pipelines, or command-line scripts.
- **Example**: `research_paper.pdf` → `research_paper.txt`

### Mode B: Structured Text (`.md`)
- **Intent**: Preserve document semantics, headings, hierarchy, lists, and formatting.
- **Features**:
  - GFM Markdown tables with proper alignment (`| Col 1 | Col 2 |`)
  - Code blocks fenced with syntax-highlighting tags (```` ```python ````)
  - Slide, sheet, and page boundaries clearly marked
  - Speech cues with timestamps
- **Example**: `presentation.pptx` → `presentation.md`

### Mode C: Complete Extraction (`.zip`)
- **Intent**: Full export bundle capturing every extracted facet of the file.
- **Output Structure**:
  ```
  report_extracted.zip
  ├── report.txt                  # Plain text representation (Mode A)
  ├── report.md                   # Structured Markdown (Mode B)
  ├── report.json                 # Complete AST schema (metadata, blocks, tables)
  ├── report.html                 # Clean, responsive HTML preview
  ├── metadata.json               # Extracted file attributes and technical specs
  ├── manifest.json               # Export audit manifest and file listing
  ├── tables/                     # Individual extracted tables as sanitized CSVs
  │   ├── table_1_Summary.csv
  │   └── table_2_Breakdown.csv
  └── subtitles/                  # Media transcripts (if audio/video source)
      ├── transcript.srt
      └── transcript.vtt
  ```

---

## 4. Key Architectural Principles

1. **Authentic Extraction, Zero Hallucination**:
   DocuMind never invents text or summarizes content during conversion. What is in the source file is what appears in the converted output.
2. **Safe Formula Handling**:
   Exported CSV files automatically sanitize formula injection vectors (`=`, `+`, `-`, `@`, `\t`, `\r`) without corrupting legitimate negative numbers (e.g. `-42.5` remains a clean number).
3. **HTML Sanitization**:
   Generated HTML files strictly escape user content to guarantee zero script execution, cross-site scripting (XSS), or malicious tag injection.
4. **Hardware-Aware & Resilient**:
   Runs efficiently on CPU fallback with optional GPU acceleration for OCR and transcription.
