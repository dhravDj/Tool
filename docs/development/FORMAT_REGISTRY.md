# File Format Registry Documentation

## 1. Overview

The central **Format Registry** (`backend/app/modules/formats/registry.py`) provides a single source of truth for all formats recognized by DocuMind AI.

It indexes formats across 17 functional categories:
1. `document` (DOCX, DOC, ODT, RTF, TXT)
2. `pdf` (PDF)
3. `spreadsheet` (XLSX, XLS, ODS, CSV, TSV)
4. `presentation` (PPTX, PPT, ODP)
5. `image` (PNG, JPEG, GIF, WEBP, BMP, TIFF, SVG)
6. `audio` (MP3, WAV, FLAC, OGG, M4A)
7. `video` (MP4, MKV, WEBM, MOV, AVI)
8. `archive` (ZIP, 7Z, TAR, GZ, BZ2, XZ, RAR)
9. `code` (PY, JS, TS, HTML, CSS, JAVA, C, CPP, SQL)
10. `structured_data` (JSON, XML, YAML, TOML, PARQUET)
11. `email` (EML, MSG)
12. `ebook` (EPUB)
13. `font` (TTF, OTF, WOFF, WOFF2)
14. `executable` (ELF, PE, MACHO)
15. `disk_image` (ISO)
16. `other_binary` (Generic binary, DAT)
17. `unknown` (Unidentified formats)

---

## 2. Detection vs Extraction Support

A core architectural principle of DocuMind AI is that **detection support and extraction support are independent properties**:

```python
class SupportStatus(StrEnum):
    DETECTED_AND_SUPPORTED = "detected_and_supported"       # Detection + full extraction supported
    DETECTED_BUT_NOT_IMPLEMENTED = "detected_but_not_implemented" # Detection supported, extraction planned
    DETECTED_BUT_UNSUPPORTED = "detected_but_unsupported"   # Detection supported, extraction out of scope (e.g. binaries/executables)
    UNKNOWN_FORMAT = "unknown_format"                       # File could not be identified
    INVALID_FILE = "invalid_file"                           # Zero-byte, non-existent, or unreadable
    CORRUPTED_FILE = "corrupted_file"                       # Truncated or malformed file structure
    SUSPICIOUS_FILE = "suspicious_file"                     # Dangerous polyglot or masqueraded executable
    AMBIGUOUS_FORMAT = "ambiguous_format"                   # Weak or conflicting signals
```

---

## 3. Format Definition Model

Each format is registered as an immutable `FileFormatDefinition`:

```python
@dataclass(frozen=True)
class FileFormatDefinition:
    format_id: str                      # Unique canonical slug (e.g. "pdf", "docx")
    canonical_name: str                 # Full name ("Portable Document Format")
    display_name: str                   # User-facing label ("PDF Document")
    category: FormatCategory            # One of the 17 format categories
    mime_types: list[str]               # All valid MIME types associated with the format
    extensions: list[str]               # Known extensions without leading dots
    magic_signatures: list[MagicSignature] = field(default_factory=list)
    is_container: bool = False          # Whether format is an archive/package container
    container_type: Optional[str] = None# "zip", "ole2", "riff", "isobmff", "tar"
    support_status: SupportStatus = SupportStatus.DETECTED_AND_SUPPORTED
    extraction_plugin_id: Optional[str] = None
    version_info: Optional[str] = None
    description: str = ""
```

---

## 4. Querying the Registry

```python
from app.modules.formats.registry import format_registry
from app.modules.formats.categories import FormatCategory

# Lookup by canonical format ID
pdf_def = format_registry.get_by_id("pdf")

# Lookup by extension
candidates = format_registry.get_by_extension("docx")

# Lookup by MIME type
candidates = format_registry.get_by_mime("application/json")

# Filter by category
all_images = format_registry.get_by_category(FormatCategory.IMAGE)

# Signature scanning
matches = format_registry.find_by_signature(buffer)
```
