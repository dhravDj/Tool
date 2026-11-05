# Adding a New File Format to DocuMind AI

This guide walks engineers through adding support for a new file format in the detection engine.

---

## 1. Register the Format Definition

Open `backend/app/modules/formats/registry.py`.

In `FormatRegistry._register_default_formats()`, add your format definition under its appropriate category:

```python
self.register(
    FileFormatDefinition(
        format_id="webp",
        canonical_name="WebP Image",
        display_name="Google WebP Image",
        category=FormatCategory.IMAGE,
        mime_types=["image/webp"],
        extensions=["webp"],
        magic_signatures=[WEBP_RIFF],
        is_container=True,
        container_type="riff",
        support_status=SupportStatus.DETECTED_AND_SUPPORTED,
        description="Modern lossy/lossless compressed web image",
    )
)
```

---

## 2. Add Binary Signatures (If Applicable)

If the format has distinctive magic bytes, declare a `MagicSignature` in `backend/app/modules/formats/signatures.py`:

```python
# Exact header match at offset 0
WEBP_RIFF = MagicSignature(
    signature_bytes=b"RIFF",
    offset=0,
)

# If format requires offset or bitmask matching:
MY_FORMAT_SIG = MagicSignature(
    signature_bytes=b"\x00\x01MYTAG",
    offset=8,
    mask=b"\xff\xff\xff\xff\xff\xff\xff",
)
```

---

## 3. Add Container Inspection Rules (If Container-Based)

If the format is packaged inside a ZIP, RIFF, or ISO-BMFF container, add inspection logic in:
`backend/app/modules/formats/container_formats.py`.

Example for ZIP-based formats:

```python
# In ContainerInspector.inspect_zip_package()
if "my_manifest.xml" in names:
    result.identified_format_id = "my_format"
    return result
```

---

## 4. Add Safe Text Heuristics (If Text-Based)

If the format is a plain text or structured markup format, add heuristic validation in:
`backend/app/modules/files/detection/text_detector.py`.

Ensure parsing is defensively bounded and never executes code.

---

## 5. Add Unit Tests and Edge Cases

Add test cases in:
1. `backend/tests/unit/test_format_registry.py`: Verify registration and lookups.
2. `backend/tests/unit/test_detection_pipeline.py`: Add specimen test verifying:
   - Valid file detection
   - Extension mismatch detection (e.g. file renamed to `.dat`)
   - Truncated or corrupted file handling

Run the test suite:
```bash
./scripts/run_tests.sh
```
