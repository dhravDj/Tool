# Security Architecture & Safeguards

DocuMind is designed with deep defense-in-depth protections to process untrusted files safely.

---

## 1. File Ingestion & Storage Defenses

- **Signature-Based Magic Byte Validation**:
  Every file is verified using raw binary header signatures before processing. File extensions are never trusted blindly. MIME-spoofed payloads (e.g. an executable renamed to `.pdf`) are rejected or flagged.
- **Path Traversal Protection**:
  Filenames are stripped of path components (`../`, `..\`) and normalized via `sanitize_filename`. Internal file paths inside ZIP, TAR, and 7Z archives are checked with `os.path.commonpath` to ensure extracted files remain within sandboxed extraction roots.
- **Zip Bomb & Archive Defenses**:
  - Maximum compression ratio threshold enforced (default: 100:1).
  - Maximum uncompressed size limit enforced (default: 500 MB per archive).
  - Maximum entry limit enforced (default: 10,000 files).
  - Maximum nesting depth enforced (default: 3 levels of nested archives).

---

## 2. Parsing & Engine Defenses

- **Zero-Execution Guarantee**:
  Uploaded source code (`.py`, `.js`, `.sh`, `.sql`, etc.) and macro-enabled documents (`.docm`, `.xlsm`, `.pptm`) are **NEVER EXECUTED**. Files are parsed strictly into Abstract Syntax Trees (AST) or token streams.
- **XML External Entity (XXE) Protection**:
  All XML, SVG, ODF, and OpenXML parsers utilize `defusedxml` to block entity expansions, billion-laughs attacks, and external DTD fetches.
- **YAML Alias Bombs**:
  YAML documents are parsed exclusively with `yaml.SafeLoader` to prevent arbitrary Python object instantiation and exponential alias expansion attacks.
- **Image Decompression Bombs**:
  Pillow `Image.MAX_IMAGE_PIXELS` limits are configured to block pixel flood decompression exploits.

---

## 3. Output Export Sanitization

### CSV Formula Injection (DDE) Neutralization
When converting content into `.csv`, DocuMind prevents formula injection attacks where cells begin with dangerous trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`):

- **Rule**:
  1. If cell starts with `=`, `@`, `\t`, or `\r`, prepend a single quote (`'`).
  2. If cell starts with `+` or `-`:
     - Test whether the string is a valid numeric literal (e.g., `-42.5`, `-100`, `+2500`).
     - If valid numeric literal: **Do not modify**. Legitimate negative numbers are preserved cleanly.
     - If non-numeric (e.g. `-2+3*cmd|' /C calc'!A0`): Prepend a single quote (`'`).

### HTML XSS Sanitization
When rendering HTML documents:
- All dynamic strings, text blocks, table cells, and captions pass through `html.escape(..., quote=True)`.
- No inline JavaScript, `<script>` tags, or external `src` frames are injected.
- Generated HTML uses standard safe CSS for layout without dangerous CSS expressions.
