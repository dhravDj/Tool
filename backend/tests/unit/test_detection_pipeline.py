"""Comprehensive test suite for Universal File Detection Pipeline.

Tests all format categories and 20 distinct real-world edge cases.
"""

import io
import tarfile
import zipfile
from pathlib import Path

from app.modules.files.detection.detector import universal_detector
from app.modules.formats.categories import FormatCategory
from app.modules.formats.support_status import ConfidenceLevel, SupportStatus

# ---------------------------------------------------------------------------
# Specimen Fixture Helpers
# ---------------------------------------------------------------------------


def create_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        zf.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships/>')
        zf.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>DocuMind</w:t></w:r></w:p></w:body></w:document>',
        )
    return buf.getvalue()


def create_xlsx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        zf.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships/>')
        zf.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )
    return buf.getvalue()


def create_pptx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        zf.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships/>')
        zf.writestr(
            "ppt/presentation.xml",
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>',
        )
    return buf.getvalue()


def create_epub_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0"/>')
    return buf.getvalue()


def create_odt_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "mimetype", "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED
        )
        zf.writestr("content.xml", "<office:document-content/>")
    return buf.getvalue()


def create_tar_bytes() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        data = b"Hello from inside TAR"
        ti = tarfile.TarInfo("test.txt")
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Category Tests
# ---------------------------------------------------------------------------


def test_detect_pdf(tmp_path: Path):
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 1 >>\nstartxref\n9\n%%EOF\n"
    f = tmp_path / "sample.pdf"
    f.write_bytes(pdf_content)

    res = universal_detector.detect_file(f, "sample.pdf")
    assert res.format_id == "pdf"
    assert res.category == FormatCategory.PDF
    assert res.mime_type == "application/pdf"
    assert res.confidence_level == ConfidenceLevel.HIGH
    assert res.is_mismatch is False
    assert res.is_valid is True


def test_detect_docx_container(tmp_path: Path):
    docx_bytes = create_docx_bytes()
    f = tmp_path / "document.docx"
    f.write_bytes(docx_bytes)

    res = universal_detector.detect_file(f, "document.docx")
    assert res.format_id == "docx"
    assert res.category == FormatCategory.DOCUMENT
    assert res.is_container is True
    assert res.container_type in ("zip", "ooxml")
    assert res.confidence_level == ConfidenceLevel.HIGH


def test_detect_xlsx_container(tmp_path: Path):
    f = tmp_path / "sheet.xlsx"
    f.write_bytes(create_xlsx_bytes())

    res = universal_detector.detect_file(f, "sheet.xlsx")
    assert res.format_id == "xlsx"
    assert res.category == FormatCategory.SPREADSHEET
    assert res.is_container is True
    assert res.container_type in ("zip", "ooxml")


def test_detect_pptx_container(tmp_path: Path):
    f = tmp_path / "slides.pptx"
    f.write_bytes(create_pptx_bytes())

    res = universal_detector.detect_file(f, "slides.pptx")
    assert res.format_id == "pptx"
    assert res.category == FormatCategory.PRESENTATION
    assert res.is_container is True


def test_detect_images_png_jpeg_gif(tmp_path: Path):
    # PNG
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x0a\x00\x00\x00\x0a\x08\x06\x00\x00\x00\x8d2\xcf\xbd\x00\x00\x00\x00IEND\xaeB`\x82"
    f_png = tmp_path / "test.png"
    f_png.write_bytes(png_bytes)
    res_png = universal_detector.detect_file(f_png, "test.png")
    assert res_png.format_id == "png"
    assert res_png.category == FormatCategory.IMAGE
    assert res_png.confidence_level == ConfidenceLevel.HIGH

    # JPEG
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    f_jpg = tmp_path / "photo.jpg"
    f_jpg.write_bytes(jpeg_bytes)
    res_jpg = universal_detector.detect_file(f_jpg, "photo.jpg")
    assert res_jpg.format_id in ("jpeg", "jpg")
    assert res_jpg.category == FormatCategory.IMAGE

    # GIF
    gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    f_gif = tmp_path / "anim.gif"
    f_gif.write_bytes(gif_bytes)
    res_gif = universal_detector.detect_file(f_gif, "anim.gif")
    assert res_gif.format_id == "gif"
    assert res_gif.category == FormatCategory.IMAGE


def test_detect_audio_wav(tmp_path: Path):
    wav_bytes = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    f = tmp_path / "audio.wav"
    f.write_bytes(wav_bytes)

    res = universal_detector.detect_file(f, "audio.wav")
    assert res.format_id == "wav"
    assert res.category == FormatCategory.AUDIO


def test_detect_archives_zip_tar(tmp_path: Path):
    # Plain ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", "Some zipped text")
    f_zip = tmp_path / "archive.zip"
    f_zip.write_bytes(buf.getvalue())
    res_zip = universal_detector.detect_file(f_zip, "archive.zip")
    assert res_zip.format_id == "zip"
    assert res_zip.category == FormatCategory.ARCHIVE
    assert res_zip.is_container is True

    # TAR
    f_tar = tmp_path / "archive.tar"
    f_tar.write_bytes(create_tar_bytes())
    res_tar = universal_detector.detect_file(f_tar, "archive.tar")
    assert res_tar.format_id == "tar"
    assert res_tar.category == FormatCategory.ARCHIVE


def test_detect_structured_data(tmp_path: Path):
    # JSON
    f_json = tmp_path / "config.json"
    f_json.write_text('{"name": "DocuMind", "status": "active", "layers": 7}')
    res_json = universal_detector.detect_file(f_json, "config.json")
    assert res_json.format_id == "json"
    assert res_json.category == FormatCategory.STRUCTURED_DATA

    # XML
    f_xml = tmp_path / "data.xml"
    f_xml.write_text('<?xml version="1.0"?><dataset><record id="1"/></dataset>')
    res_xml = universal_detector.detect_file(f_xml, "data.xml")
    assert res_xml.format_id == "xml"
    assert res_xml.category == FormatCategory.STRUCTURED_DATA

    # TOML
    f_toml = tmp_path / "settings.toml"
    f_toml.write_text('[server]\nhost = "127.0.0.1"\nport = 8000\n')
    res_toml = universal_detector.detect_file(f_toml, "settings.toml")
    assert res_toml.format_id == "toml"
    assert res_toml.category == FormatCategory.STRUCTURED_DATA


def test_detect_programming_languages(tmp_path: Path):
    # Python
    f_py = tmp_path / "main.py"
    f_py.write_text(
        "import sys\n\ndef run():\n    print('DocuMind')\n\nif __name__ == '__main__':\n    run()\n"
    )
    res_py = universal_detector.detect_file(f_py, "main.py")
    assert res_py.format_id == "py"
    assert res_py.category == FormatCategory.CODE

    # SQL
    f_sql = tmp_path / "query.sql"
    f_sql.write_text("SELECT id, name FROM files WHERE status = 'stored' ORDER BY id DESC;")
    res_sql = universal_detector.detect_file(f_sql, "query.sql")
    assert res_sql.format_id == "sql"
    assert res_sql.category == FormatCategory.CODE


# ---------------------------------------------------------------------------
# 20 Distinct Real-World Edge Cases
# ---------------------------------------------------------------------------


def test_edge_case_1_missing_extension(tmp_path: Path):
    """File has no extension at all, but is actually a valid PDF."""
    pdf_content = b"%PDF-1.5\n%trailer\n%%EOF"
    f = tmp_path / "no_extension_doc"
    f.write_bytes(pdf_content)

    res = universal_detector.detect_file(f, "no_extension_doc")
    assert res.format_id == "pdf"
    assert res.category == FormatCategory.PDF
    assert res.claimed_extension is None
    assert res.extension == "pdf"
    assert res.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)


def test_edge_case_2_extension_mismatch(tmp_path: Path):
    """PDF file renamed to .jpg: system MUST detect mismatch and identify actual PDF."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
    f = tmp_path / "scam_image.jpg"
    f.write_bytes(pdf_content)

    res = universal_detector.detect_file(f, "scam_image.jpg")
    assert res.format_id == "pdf"
    assert res.is_mismatch is True
    assert res.claimed_extension == "jpg"
    assert res.extension == "pdf"
    assert any("mismatch" in w.lower() for w in res.warnings)


def test_edge_case_3_empty_zero_byte_file(tmp_path: Path):
    """Empty 0-byte file: must be flagged as invalid."""
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")

    res = universal_detector.detect_file(f, "empty.txt")
    assert res.is_valid is False
    assert res.support_status in (SupportStatus.INVALID_FILE, SupportStatus.CORRUPTED_FILE)
    assert any("empty" in w.lower() for w in res.warnings)


def test_edge_case_4_corrupted_pdf(tmp_path: Path):
    """Corrupted PDF: truncated after header."""
    f = tmp_path / "corrupt.pdf"
    f.write_bytes(b"%PDF-1.7\nRandom incomplete bytes...")

    res = universal_detector.detect_file(f, "corrupt.pdf")
    assert res.format_id == "pdf"
    assert res.is_corrupted is True
    assert any("corrupted" in w.lower() or "truncated" in w.lower() for w in res.warnings)


def test_edge_case_5_truncated_png(tmp_path: Path):
    """PNG header without IEND terminator."""
    f = tmp_path / "broken.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + bytes(20))

    res = universal_detector.detect_file(f, "broken.png")
    assert res.format_id == "png"
    assert res.is_corrupted is True


def test_edge_case_6_invalid_zip(tmp_path: Path):
    """Malformed ZIP header."""
    f = tmp_path / "bad.zip"
    f.write_bytes(b"PK\x03\x04truncated junk")

    res = universal_detector.detect_file(f, "bad.zip")
    assert res.format_id == "zip"
    assert res.is_corrupted is True


def test_edge_case_7_generic_zip_renamed_to_docx(tmp_path: Path):
    """Regular zip file named document.docx: container inspector must flag missing word structure."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("notes.txt", "I am just a text file inside a zip")
    f = tmp_path / "fake.docx"
    f.write_bytes(buf.getvalue())

    res = universal_detector.detect_file(f, "fake.docx")
    assert res.format_id == "zip"
    assert res.is_mismatch is True
    assert res.claimed_extension == "docx"
    assert res.extension == "zip"


def test_edge_case_8_docx_renamed_to_txt(tmp_path: Path):
    """Real DOCX renamed to document.txt: must identify DOCX container despite txt extension."""
    f = tmp_path / "disguised.txt"
    f.write_bytes(create_docx_bytes())

    res = universal_detector.detect_file(f, "disguised.txt")
    assert res.format_id == "docx"
    assert res.is_mismatch is True
    assert res.claimed_extension == "txt"
    assert res.extension == "docx"


def test_edge_case_9_unknown_binary(tmp_path: Path):
    """Random unclassified bytes without any magic signature."""
    f = tmp_path / "unknown.dat"
    f.write_bytes(bytes([i % 256 for i in range(1000)]))

    res = universal_detector.detect_file(f, "unknown.dat")
    assert res.format_id in ("binary", "unknown")
    assert res.category in (FormatCategory.OTHER_BINARY, FormatCategory.UNKNOWN)


def test_edge_case_10_utf8_bom_text(tmp_path: Path):
    """UTF-8 file starting with BOM."""
    f = tmp_path / "bom.txt"
    f.write_bytes(b"\xef\xbb\xbfHello world with UTF-8 BOM")

    res = universal_detector.detect_file(f, "bom.txt")
    assert res.format_id == "txt"
    assert res.metadata.get("encoding") == "utf-8-sig"


def test_edge_case_11_utf16_le_text(tmp_path: Path):
    """UTF-16 LE file with BOM."""
    f = tmp_path / "utf16.txt"
    f.write_bytes(b"\xff\xfeH\x00e\x00l\x00l\x00o\x00")

    res = universal_detector.detect_file(f, "utf16.txt")
    assert res.format_id == "txt"
    assert res.metadata.get("encoding") == "utf-16-le"


def test_edge_case_12_unicode_filename(tmp_path: Path):
    """Filename containing multilingual Unicode characters and emojis."""
    unicode_name = "报告_документ_🚀.pdf"
    f = tmp_path / unicode_name
    f.write_bytes(b"%PDF-1.4\n%%EOF")

    res = universal_detector.detect_file(f, unicode_name)
    assert res.format_id == "pdf"
    assert res.is_valid is True


def test_edge_case_13_shell_metacharacters_in_filename(tmp_path: Path):
    """Filename with potential shell injection characters."""
    bad_name = "file;rm -rf;$(calc).txt"
    f = tmp_path / bad_name
    f.write_text("Safe text content")

    res = universal_detector.detect_file(f, bad_name)
    assert res.format_id == "txt"
    assert res.is_valid is True


def test_edge_case_14_epub_ebook(tmp_path: Path):
    """Valid EPUB package identification."""
    f = tmp_path / "book.epub"
    f.write_bytes(create_epub_bytes())

    res = universal_detector.detect_file(f, "book.epub")
    assert res.format_id == "epub"
    assert res.category == FormatCategory.EBOOK
    assert res.is_container is True


def test_edge_case_15_odt_document(tmp_path: Path):
    """Valid ODT OpenDocument Text identification."""
    f = tmp_path / "doc.odt"
    f.write_bytes(create_odt_bytes())

    res = universal_detector.detect_file(f, "doc.odt")
    assert res.format_id == "odt"
    assert res.category == FormatCategory.DOCUMENT
    assert res.is_container is True


def test_edge_case_16_executable_elf(tmp_path: Path):
    """Linux ELF executable binary detection."""
    elf_bytes = b"\x7fELF\x02\x01\x01\x00" + bytes(56)
    f = tmp_path / "program.bin"
    f.write_bytes(elf_bytes)

    res = universal_detector.detect_file(f, "program.bin")
    assert res.format_id == "elf"
    assert res.category == FormatCategory.EXECUTABLE
    assert res.support_status == SupportStatus.DETECTED_BUT_UNSUPPORTED


def test_edge_case_17_executable_pe(tmp_path: Path):
    """Windows PE executable binary detection."""
    pe_bytes = (
        b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        + bytes(48)
        + (64).to_bytes(4, "little")
        + b"PE\x00\x00"
        + bytes(20)
    )
    f = tmp_path / "setup.exe"
    f.write_bytes(pe_bytes)

    res = universal_detector.detect_file(f, "setup.exe")
    assert res.format_id == "pe"
    assert res.category == FormatCategory.EXECUTABLE


def test_edge_case_18_csv_spreadsheet(tmp_path: Path):
    """CSV text file identification as spreadsheet."""
    f = tmp_path / "data.csv"
    f.write_text("id,name,department,salary\n1,Alice,Engineering,150000\n2,Bob,Product,140000\n")

    res = universal_detector.detect_file(f, "data.csv")
    assert res.format_id == "csv"
    assert res.category == FormatCategory.SPREADSHEET


def test_edge_case_19_svg_vector_graphic(tmp_path: Path):
    """SVG graphic identification as image category."""
    f = tmp_path / "icon.svg"
    f.write_text(
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    )

    res = universal_detector.detect_file(f, "icon.svg")
    assert res.format_id == "svg"
    assert res.category == FormatCategory.IMAGE


def test_edge_case_20_compound_extension_tar_gz(tmp_path: Path):
    """Compound extension .tar.gz preservation and archive categorization."""
    f = tmp_path / "bundle.tar.gz"
    f.write_bytes(
        b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    res = universal_detector.detect_file(f, "bundle.tar.gz")
    assert res.category == FormatCategory.ARCHIVE
    assert res.extension in ("tar.gz", "gz")
