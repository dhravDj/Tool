"""Hypothesis property-based fuzzing tests for Universal File Detection Pipeline."""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.modules.files.detection.detector import universal_detector
from app.modules.formats.categories import FormatCategory
from app.modules.formats.support_status import ConfidenceLevel, SupportStatus


@given(
    data=st.binary(min_size=0, max_size=32768),
    filename=st.text(min_size=1, max_size=50).filter(lambda s: "/" not in s and "\x00" not in s),
)
@settings(max_examples=50, deadline=1000)
def test_hypothesis_arbitrary_binary_never_crashes(tmp_path_factory, data: bytes, filename: str):
    """Property: The detection pipeline must never raise an unhandled exception on arbitrary byte inputs."""
    temp_dir = tmp_path_factory.mktemp("hypo")
    # Sanitize filename for local filesystem
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename) or "file.bin"
    if safe_name in (".", ".."):
        safe_name = "file.bin"
    file_path = temp_dir / safe_name
    file_path.write_bytes(data)

    result = universal_detector.detect_file(file_path, safe_name)

    # Invariants that must ALWAYS hold
    assert isinstance(result.format_id, str)
    assert len(result.format_id) > 0
    assert 0.0 <= result.confidence_score <= 1.0
    assert isinstance(result.category, FormatCategory)
    assert isinstance(result.confidence_level, ConfidenceLevel)
    assert isinstance(result.support_status, SupportStatus)
    assert isinstance(result.is_valid, bool)
    assert isinstance(result.is_mismatch, bool)
    assert isinstance(result.is_corrupted, bool)
    assert isinstance(result.is_suspicious, bool)
    assert isinstance(result.warnings, list)
    assert isinstance(result.evidence, list)


@given(
    garbage=st.binary(min_size=0, max_size=8192),
    ext=st.sampled_from(["pdf", "png", "jpg", "docx", "xlsx", "zip", "txt", "exe", "dat"]),
)
@settings(max_examples=30, deadline=1000)
def test_hypothesis_prefixed_magic_bytes_robustness(tmp_path_factory, garbage: bytes, ext: str):
    """Property: Files starting with valid signatures followed by garbage must be processed gracefully."""
    temp_dir = tmp_path_factory.mktemp("magic_fuzz")
    png_header = b"\x89PNG\r\n\x1a\n"
    f = temp_dir / f"fuzzed.{ext}"
    f.write_bytes(png_header + garbage)

    result = universal_detector.detect_file(f, f.name)

    assert isinstance(result.format_id, str)
    if result.format_id == "png":
        # If recognized as PNG but missing proper structure, corruption flag is set
        if len(garbage) < 25 or b"IEND" not in garbage:
            assert result.is_corrupted is True
