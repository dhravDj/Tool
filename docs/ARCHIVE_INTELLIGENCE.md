# DocuMind AI — Archive & Nested File Processing Engine

## 1. Overview

The **Archive & Nested File Processing Engine (Phase 10)** extends DocuMind AI to safely inspect, extract, validate, analyze, and recursively unpack compressed multi-file archives. It acts as an intake gateway and recursive router for the entire DocuMind AI intelligence platform.

By combining format identification, multi-layered security guards, sandboxed directory extraction, and deterministic provenance tracking, the engine ingests complex multi-layer archives and orchestrates downstream processing across Documents, Images, Spreadsheets, Presentations, Audio, Video, Code, and Structured Data.

---

## 2. Supported Formats & Dispatch

The Archive Intelligence Engine provides full support for 10 compressed archive formats:

| Format ID | Format Name | Extensions | Inspector Implementation | Extractor Strategy | Magic Bytes Signature |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `zip` | ZIP Archive | `.zip` | `ZipInspector` | Python `zipfile` safe streaming | `PK\x03\x04`, `PK\x05\x06`, `PK\x07\x08` |
| `7z` | 7-Zip Archive | `.7z` | `SevenZipInspector` | `py7zr` isolated staging | `7z\xbc\xaf'\x1c` |
| `tar` | POSIX TAR Archive | `.tar` | `TarInspector` | Python `tarfile` safe member iter | `ustar\x00` / `ustar  \x00` at offset 257 |
| `tar.gz` | Gzip-Compressed TAR | `.tar.gz` | `TarInspector` | Gzip decompress + tar streaming | `\x1f\x8b` |
| `tgz` | Gzip-Compressed TAR (Alias) | `.tgz` | `TarInspector` | Gzip decompress + tar streaming | `\x1f\x8b` |
| `gz` | Standalone Gzip File | `.gz` | `GzipInspector` | Python `gzip` single stream decompress | `\x1f\x8b` |
| `tar.bz2` | Bzip2-Compressed TAR | `.tar.bz2` | `TarInspector` | Bzip2 decompress + tar streaming | `BZh` |
| `tbz2` | Bzip2 TAR (Alias) | `.tbz2`, `.tbz` | `TarInspector` | Bzip2 decompress + tar streaming | `BZh` |
| `tar.xz` | XZ-Compressed TAR | `.tar.xz` | `TarInspector` | LZMA/XZ decompress + tar streaming | `\xfd7zXZ\x00` |
| `txz` | XZ TAR (Alias) | `.txz` | `TarInspector` | LZMA/XZ decompress + tar streaming | `\xfd7zXZ\x00` |

---

## 3. Core Architectural Components

1. **`ArchiveInspectorRegistry` (`backend/app/modules/archive_intelligence/inspectors/registry.py`):**
   Dispatches files via magic byte inspection and extension heuristics without full extraction.
2. **`PathSecurityValidator` (`backend/app/modules/archive_intelligence/safety.py`):**
   Defends against directory traversal (Zip Slip `../`), absolute paths, Windows drive references, and null-byte injection.
3. **`ExtractionQuotaTracker` (`backend/app/modules/archive_intelligence/safety.py`):**
   Enforces memory quotas, max entry count, max single file size, max cumulative extraction size, and compression ratio limits.
4. **`SafeArchiveExtractor` (`backend/app/modules/archive_intelligence/extractors/safe_extractor.py`):**
   Executes safe file extraction into isolated temporary workspaces, computes SHA256 checksums, and filters blocked entries.
5. **`ArchiveHierarchyBuilder` (`backend/app/modules/archive_intelligence/hierarchy.py`):**
   Constructs normalized tree hierarchies, handling Unicode characters, case collisions, and duplicate entry names.
6. **`ArchiveIntelligencePipeline` (`backend/app/modules/archive_intelligence/pipeline.py`):**
   Coordinates execution modes, database persistence, recursive extraction, and downstream intelligence engine routing.
7. **8 Export Generators (`backend/app/modules/archive_intelligence/generators/`):**
   Produces JSON, Markdown, Plain Text, Manifest CSV, Hierarchy Tree ASCII, Extraction Report, Security Report, and Child Manifest.

---

## 4. Processing Modes

The pipeline supports 4 distinct execution modes:

- **Mode A: Inspect Only (`mode_a_inspect_only`):**
  Parses headers, inventories entries, calculates compression ratios, and renders the hierarchy tree without writing unpacked files to storage.
- **Mode B: Extract Only (`mode_b_extract_only`):**
  Safely extracts all benign archive members into storage and records file metadata and provenance relationships, without invoking downstream intelligence analyzers.
- **Mode C: Extract & Analyze (`mode_c_extract_and_analyze` — Default):**
  Extracts benign archive members and automatically dispatches each extracted file to its corresponding DocuMind AI intelligence engine:
  - Document/PDF files $\to$ Phase 3 Document Extraction
  - Image files $\to$ Phase 4 Visual Intelligence
  - Spreadsheet files $\to$ Phase 5 Spreadsheet Intelligence
  - Presentation files $\to$ Phase 6 Presentation Intelligence
  - Audio files $\to$ Phase 7 Audio Intelligence
  - Video files $\to$ Phase 8 Video Intelligence
  - Code & Structured Data $\to$ Phase 9 Code & Structured Data Intelligence
  - Nested Archives $\to$ Phase 10 recursively
- **Mode D: Selective Extraction (`mode_d_selective_analysis`):**
  Extracts and analyzes only user-specified entry IDs, reducing latency and resource utilization on large multi-gigabyte archives.

---

## 5. Provenance & Parent-Child Relationships

Every extracted file is tracked in the database with bidirectional relational linkage:
- `ArchiveAnalysisRecord`: Stores top-level archive summary, safety audit, compression stats, and artifact paths.
- `ArchiveEntryRecord`: Tracks entry-level metadata, compression method, encryption flag, CRC32, and processing status.
- `ArchiveRelationshipRecord`: Maintains parent-child file IDs, nesting depth, and entry paths for full provenance audits.
