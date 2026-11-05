# Detection Engine Testing Strategy & Quality Assurance

## 1. Test Suite Architecture

The DocuMind AI detection engine includes an exhaustive, multi-tier testing suite ensuring robustness, correctness, security, and performance:

| Test Module | Scope | Test Count | Description |
| :--- | :--- | :--- | :--- |
| `test_format_registry.py` | Unit | 7 | Tests format registration, category indexing, MIME lookups, extension matching, and signature scan. |
| `test_detection_pipeline.py` | Unit | 29 | Comprehensive category specimens (PDF, DOCX, XLSX, PPTX, PNG, JPG, GIF, WAV, ZIP, TAR, JSON, XML, TOML, Python, SQL) and 20 distinct real-world edge cases. |
| `test_detection_hypothesis.py` | Unit (Fuzzing) | 2 (80 iterations) | Property-based fuzzing with Hypothesis generating arbitrary binary strings and validating pipeline robustness with zero crashes. |
| `test_detection_api.py` | Integration | 6 | API verification for `/api/v1/formats`, `/api/v1/system/detection-capabilities`, `/api/v1/files/detect`, `/api/v1/files/detect/batch`, and persisted file retrieval. |
| **Total Backend Tests** | **All** | **67** | **100% passing in 2.7 seconds.** |

---

## 2. 20 Real-World Edge Cases Tested

The pipeline specifically validates 20 edge cases:

1. **Missing extension:** File has no extension, detected correctly via binary signature.
2. **Extension mismatch:** PDF disguised as `.jpg`, detected with `is_mismatch=True`.
3. **Empty file:** Zero-byte file rejected with `is_valid=False` and status `INVALID_FILE`.
4. **Corrupted PDF:** Truncated PDF lacking `%%EOF`, flagged with `is_corrupted=True`.
5. **Truncated PNG:** PNG header lacking `IEND` chunk, flagged with `is_corrupted=True`.
6. **Invalid ZIP:** Malformed ZIP header flagged with `is_corrupted=True`.
7. **Generic ZIP renamed to `.docx`:** Flagged as missing OOXML structure with `is_mismatch=True`.
8. **DOCX renamed to `.txt`:** Correctly identified as DOCX container with `is_mismatch=True`.
9. **Unknown binary:** Arbitrary bytes without magic signature classified as `binary`/`unknown`.
10. **UTF-8 BOM:** Text with `\xef\xbb\xbf` correctly detected with `encoding="utf-8-sig"`.
11. **UTF-16 LE:** Text with `\xff\xfe` correctly detected with `encoding="utf-16-le"`.
12. **Unicode filename:** Multilingual characters and emojis (`报告_документ_🚀.pdf`) handled safely.
13. **Shell metacharacters:** Filenames containing `;rm -rf;$(calc)` sanitized without code execution.
14. **EPUB E-Book:** OCF container and mimetype entry identified as `ebook`.
15. **ODT Document:** OpenDocument Text container identified as `document`.
16. **Linux ELF Executable:** `\x7fELF` detected as `executable` with `DETECTED_BUT_UNSUPPORTED`.
17. **Windows PE Executable:** `MZ` + `PE` header detected as `executable`.
18. **CSV Delimited Data:** Tabular text classified into `spreadsheet` category.
19. **SVG Vector Graphic:** XML vector structure classified into `image` category.
20. **Compound Extensions:** `.tar.gz` preservation and archive categorization.

---

## 3. Running Tests and Benchmarks

### Running the complete automated quality suite:
```bash
./scripts/run_tests.sh
```

### Running the standalone performance benchmark:
```bash
.venv/bin/python scripts/benchmark_detection.py
```
