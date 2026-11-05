"""Unit tests for the File Format Registry."""

from app.modules.formats.categories import FormatCategory
from app.modules.formats.registry import format_registry
from app.modules.formats.support_status import SupportStatus


def test_registry_initialization():
    """Verify registry loads all default format definitions across categories."""
    formats = format_registry.list_all()
    assert len(formats) >= 40, f"Expected at least 40 formats, got {len(formats)}"

    categories = format_registry.list_categories()
    assert len(categories) >= 15


def test_get_by_id():
    """Verify retrieval by canonical format ID."""
    pdf = format_registry.get_by_id("pdf")
    assert pdf is not None
    assert pdf.format_id == "pdf"
    assert pdf.category == FormatCategory.PDF
    assert "application/pdf" in pdf.mime_types

    docx = format_registry.get_by_id("docx")
    assert docx is not None
    assert docx.is_container is True
    assert docx.container_type == "zip"


def test_get_by_extension():
    """Verify extension lookups (case-insensitive, with or without dot)."""
    assert len(format_registry.get_by_extension("pdf")) > 0
    assert len(format_registry.get_by_extension(".PDF")) > 0
    assert len(format_registry.get_by_extension("docx")) > 0
    assert (
        len(format_registry.get_by_extension("tar.gz")) > 0
        or len(format_registry.get_by_extension("gz")) > 0
    )
    assert len(format_registry.get_by_extension("nonexistent_extension_xyz")) == 0


def test_get_by_mime():
    """Verify MIME type lookups."""
    fmts = format_registry.get_by_mime("image/png")
    assert len(fmts) > 0
    assert fmts[0].format_id == "png"

    fmts = format_registry.get_by_mime("application/json")
    assert len(fmts) > 0
    assert fmts[0].format_id == "json"


def test_get_by_category():
    """Verify category filtering."""
    images = format_registry.get_by_category(FormatCategory.IMAGE)
    assert len(images) >= 6
    extensions = [ext for fmt in images for ext in fmt.extensions]
    assert "png" in extensions
    assert "jpg" in extensions or "jpeg" in extensions


def test_support_status_distinction():
    """Verify that detection support is separate from extraction support."""
    pdf = format_registry.get_by_id("pdf")
    assert pdf is not None
    assert pdf.support_status == SupportStatus.DETECTED_AND_SUPPORTED

    elf = format_registry.get_by_id("elf")
    assert elf is not None
    assert elf.support_status == SupportStatus.DETECTED_BUT_UNSUPPORTED


def test_signature_matching():
    """Verify binary signature registry matching."""
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    matches = format_registry.find_by_signature(png_header)
    assert len(matches) > 0
    assert matches[0].format_id == "png"

    pdf_header = b"%PDF-1.7\n%raw content"
    matches = format_registry.find_by_signature(pdf_header)
    assert len(matches) > 0
    assert matches[0].format_id == "pdf"
