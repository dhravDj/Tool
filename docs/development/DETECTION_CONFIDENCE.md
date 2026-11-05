# Multi-Signal Confidence Arbitration & Risk Scoring

## 1. Architectural Philosophy

DocuMind AI operates on a **zero-trust model** for uploaded files. Filename extensions can be trivially spoofed, altered, or omitted. Therefore, the detection engine gathers independent signals across 5 detection layers:

1. `MAGIC_SIGNATURE` (Binary magic bytes)
2. `MIME_DETECTOR` (libmagic binary inspection)
3. `CONTAINER_MANIFEST` (Internal package structure)
4. `TEXT_PARSER` (Defensive syntax parsing: JSON, XML, TOML, CSV, Code)
5. `EXTENSION_HINT` (Filename extension)

---

## 2. Signal Precedence Hierarchy

When signals conflict, the `ConfidenceEvaluator` resolves candidates based on deterministic architectural authority:

```
Container Structure (OOXML / ODF / EPUB manifest)
         │
         ▼
Specific Binary Signature (Magic Bytes at offset 0 / header)
         │
         ▼
Safe Structured Text Syntax (Strict JSON / XML / TOML parser)
         │
         ▼
libmagic MIME Type Introspection
         │
         ▼
Filename Extension (Weakest Hint)
```

---

## 3. Confidence Level & Numerical Score

Every detection produces both a numerical confidence score (`0.0` to `1.0`) and a categorical `ConfidenceLevel`:

| Confidence Level | Score Range | Typical Criteria |
| :--- | :--- | :--- |
| **HIGH** | `0.85 – 0.98` | Multiple independent signals agree (e.g. Magic byte + MIME match, or verified internal container structure). |
| **MEDIUM** | `0.70 – 0.84` | Strong single signal present (e.g. valid strict JSON syntax, or uncompressed text with verified BOM). |
| **LOW** | `0.30 – 0.69` | Weak signals or single unconfirmed heuristic (e.g. ASCII with basic delimiters, or extension-only match). |
| **UNKNOWN** | `0.00` | Unidentifiable binary data, empty file, or non-existent file. |

---

## 4. Extension Mismatch Detection

If a file's claimed extension does not match the canonical extension list for the detected binary format, the engine:

1. Sets `is_mismatch = True`.
2. Generates an explicit warning:
   `"Extension mismatch: filename claims 'jpg', but binary evidence indicates 'pdf' (Portable Document Format)."`
3. Retains `claimed_extension` and `extension` separately in the API response and database record.
4. Allows downstream processing to route the file according to its **true format** rather than its deceptive extension.

---

## 5. Security & Risk Flags

- **`is_corrupted = True`**: Flagged when a recognized binary lacks mandatory end markers (e.g. PDF lacking `%%EOF`, PNG lacking `IEND`, or ZIP with broken headers).
- **`is_suspicious = True`**: Flagged when:
  - An executable binary (ELF, PE, Mach-O) is disguised with an innocuous extension.
  - A ZIP file exhibits a compression ratio exceeding 150:1 (potential zip bomb).
  - Multiple contradictory binary signatures are discovered (polyglot files).
