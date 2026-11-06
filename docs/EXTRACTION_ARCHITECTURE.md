# Universal Extraction Architecture

## 1. Architectural Pipeline

The extraction architecture is built on a clean pipeline decoupling input detection, domain-specific extraction, normalized content representation, and output generation.

```
┌────────────────────────────────────────────────────────┐
│               1. Multi-Signal Detection                │
│    Signature Magic Bytes → Container Parser → MIME     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               2. Extraction Router Layer               │
│     Directs to 1 of 9 Domain Extraction Pipelines     │
└─────┬──────┬──────┬──────┬─────┬──────┬─────┬─────┬────┘
      │      │      │      │     │      │     │     │
      ▼      ▼      ▼      ▼     ▼      ▼     ▼     ▼
    [Doc] [Sheet] [Pres] [Image][Audio][Video][Code][Data][Archive]
      │      │      │      │     │      │     │     │     │
      └──────┴──────┴──────┴─────┴──────┴─────┴─────┴─────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             3. Universal Adapter Layer                 │
│         Maps Engine Models → UniversalContent          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              4. Output Converter Layer                 │
│   Mode A (TXT) │ Mode B (MD) │ Mode C (ZIP) │ CSV │ HTML│
└────────────────────────────────────────────────────────┘
```

---

## 2. Standardized Content Representation (`UniversalContent`)

Every file format, regardless of its original binary or structured representation, is normalized into `UniversalContent`:

```python
class UniversalContent(BaseModel):
    source_filename: str
    source_format: str
    title: str = ""
    author: str = ""
    page_count: int = 1
    word_count: int = 0
    paragraphs: list[str] = Field(default_factory=list)
    sections: list[UniversalSection] = Field(default_factory=list)
    tables: list[UniversalTable] = Field(default_factory=list)
    code_blocks: list[UniversalCodeBlock] = Field(default_factory=list)
    transcript_segments: list[UniversalTranscriptSegment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    raw_text: str = ""
```

### Component Models:
- **`UniversalTable`**: Preserves sheet name/title, typed headers, and row data as 2D string matrices with row and column counts.
- **`UniversalSection`**: Encapsulates document headings (levels 1–6), page or slide numbers, and paragraph content.
- **`UniversalCodeBlock`**: Contains raw unmodified code text, language identifier, and line counts.
- **`UniversalTranscriptSegment`**: Preserves audio/video speech start/end seconds, speaker turns, and transcription confidence.

---

## 3. Format Engine Adapters

1. **DocumentAdapter**: Maps `CanonicalDocument` blocks into sections, headings, tables, and paragraphs.
2. **SpreadsheetAdapter**: Flattens multi-sheet workbooks into individual `UniversalTable` instances and statistical summaries.
3. **PresentationAdapter**: Converts slide sequences into sections with titles, bullets, speaker notes, and embedded tables.
4. **ImageAdapter**: Formats genuine Tesseract OCR text blocks and bounding-box coordinates.
5. **AudioAdapter**: Maps ASR speech tokens and time-aligned segments with speaker diarization.
6. **VideoAdapter**: Pairs audio speech transcripts with temporal visual scene cut markers and keyframe summaries.
7. **CodeAdapter**: Emits syntax AST symbols alongside unaltered original code text.
8. **StructuredDataAdapter**: Formats hierarchical JSON/YAML/TOML configurations and columnar Parquet tables.
9. **ArchiveAdapter**: Extracts directory trees, entry manifests, compression ratios, and safe child file links.
