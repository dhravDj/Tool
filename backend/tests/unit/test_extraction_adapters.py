"""Unit tests for document extraction adapters across all supported formats."""

import zipfile
from pathlib import Path

import docx
import pymupdf
import pytest
from ebooklib import epub

from app.domain.enums import BlockType, ExtractionStatus
from app.modules.extraction.adapters import (
    DocxExtractor,
    EPUBExtractor,
    LegacyDocExtractor,
    MarkdownExtractor,
    ODTExtractor,
    PageLimitExceededError,
    PasswordRequiredError,
    PDFExtractor,
    PlainTextExtractor,
    RTFExtractor,
)
from app.modules.extraction.generators.json_generator import JSONGenerator
from app.modules.extraction.generators.manifest_generator import ManifestGenerator
from app.modules.extraction.generators.markdown_generator import MarkdownGenerator
from app.modules.extraction.pipeline import extraction_pipeline


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


# ==============================================================================
# 1. PDF Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_pdf_extractor_native_text_and_metadata(temp_dir: Path) -> None:
    pdf_path = temp_dir / "sample.pdf"
    doc = pymupdf.open()
    doc.set_metadata(
        {
            "title": "Corporate Annual Strategy",
            "author": "Jane Doe",
            "subject": "Strategic Planning",
        }
    )
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 60), "Executive Summary", fontsize=18)
    page.insert_text((50, 120), "DocuMind AI provides universal file intelligence.", fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    canonical_doc = await extractor.extract_document(pdf_path, "sample.pdf")

    assert canonical_doc.detected_format == "pdf"
    assert canonical_doc.page_count == 1
    assert canonical_doc.metadata["title"] == "Corporate Annual Strategy"
    assert canonical_doc.metadata["author"] == "Jane Doe"
    assert len(canonical_doc.blocks) >= 2

    # Verify block content and bounding boxes
    texts = [b.text for b in canonical_doc.blocks]
    assert any("Executive Summary" in t for t in texts)
    assert any("DocuMind AI" in t for t in texts)
    assert canonical_doc.blocks[0].bounding_box is not None
    assert len(canonical_doc.blocks[0].bounding_box) == 4


@pytest.mark.asyncio
async def test_pdf_extractor_table_extraction(temp_dir: Path) -> None:
    pdf_path = temp_dir / "table_doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((50, 50), "Financial Performance Table", fontsize=16)

    # Insert table text
    page.insert_text((50, 100), "Quarter   Revenue   Profit", fontsize=11)
    page.insert_text((50, 120), "Q1        $10M      $2M", fontsize=11)
    page.insert_text((50, 140), "Q2        $14M      $3.5M", fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    canonical_doc = await extractor.extract_document(pdf_path, "table_doc.pdf")
    assert canonical_doc.extraction_status in (
        ExtractionStatus.COMPLETED,
        ExtractionStatus.COMPLETED_WITH_WARNINGS,
    )
    assert len(canonical_doc.blocks) >= 1


@pytest.mark.asyncio
async def test_pdf_extractor_encrypted_password_handling(temp_dir: Path) -> None:
    enc_path = temp_dir / "encrypted.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Confidential Board Minutes")
    doc.save(str(enc_path), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="pass123")
    doc.close()

    extractor = PDFExtractor()

    # 1. Without password -> raises PasswordRequiredError
    with pytest.raises(PasswordRequiredError):
        await extractor.extract_document(enc_path, "encrypted.pdf")

    # 2. With wrong password -> raises PasswordRequiredError
    with pytest.raises(PasswordRequiredError):
        await extractor.extract_document(enc_path, "encrypted.pdf", options={"password": "wrong"})

    # 3. With correct password -> extracts successfully
    doc_unlocked = await extractor.extract_document(
        enc_path, "encrypted.pdf", options={"password": "pass123"}
    )
    assert doc_unlocked.extraction_status == ExtractionStatus.COMPLETED
    assert any("Confidential Board Minutes" in b.text for b in doc_unlocked.blocks)


@pytest.mark.asyncio
async def test_pdf_extractor_page_limit_exceeded(temp_dir: Path) -> None:
    pdf_path = temp_dir / "long.pdf"
    doc = pymupdf.open()
    for _ in range(5):
        doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    # Test setting a strict max limit of 3 pages
    with pytest.raises(PageLimitExceededError):
        await extractor.extract_document(pdf_path, "long.pdf", options={"max_page_limit": 3})


# ==============================================================================
# 2. DOCX Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_docx_extractor(temp_dir: Path) -> None:
    docx_path = temp_dir / "test.docx"
    doc = docx.Document()
    doc.core_properties.title = "System Architecture Document"
    doc.core_properties.author = "Principal Engineer"

    # Add headings and body
    doc.add_heading("Section 1: Introduction", level=1)
    doc.add_paragraph("This document describes the high-level architecture of DocuMind AI.")
    doc.add_heading("Section 1.1: Core Components", level=2)
    doc.add_paragraph("First component: Ingestion engine.")

    # Add bullet list
    doc.add_paragraph("FastAPI Backend", style="List Bullet")
    doc.add_paragraph("PostgreSQL Database", style="List Bullet")

    # Add table
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Target"
    table.cell(1, 0).text = "Latency"
    table.cell(1, 1).text = "< 200ms"

    doc.save(str(docx_path))

    extractor = DocxExtractor()
    canonical_doc = await extractor.extract_document(docx_path, "test.docx")

    assert canonical_doc.detected_format == "docx"
    assert canonical_doc.metadata["title"] == "System Architecture Document"
    assert canonical_doc.metadata["author"] == "Principal Engineer"
    assert canonical_doc.page_count >= 1

    # Check headings
    heading_blocks = [b for b in canonical_doc.blocks if b.block_type == BlockType.HEADING]
    assert len(heading_blocks) >= 2
    assert heading_blocks[0].metadata.get("heading_level") == 1
    assert "Section 1: Introduction" in heading_blocks[0].text

    # Check list items
    list_blocks = [b for b in canonical_doc.blocks if b.block_type == BlockType.LIST_ITEM]
    assert len(list_blocks) >= 2

    # Check table block
    table_blocks = [b for b in canonical_doc.blocks if b.block_type == BlockType.TABLE]
    assert len(table_blocks) == 1
    assert "Metric" in table_blocks[0].text
    assert table_blocks[0].metadata["table_grid"] == [["Metric", "Target"], ["Latency", "< 200ms"]]


# ==============================================================================
# 3. Legacy DOC Extractor Tests
# ==============================================================================


def create_synthetic_doc_bytes(text: str) -> bytes:
    """Generate a minimal valid OLE2 compound document containing a WordDocument stream."""
    import struct

    content = (text * 120).encode("utf-16le")
    pad_len = 512 - (len(content) % 512) if len(content) % 512 else 0
    content_padded = content + b"\x00" * pad_len
    num_sectors = len(content_padded) // 512

    header = bytearray(512)
    header[0:8] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    header[24:26] = b"\x3e\x00"
    header[26:28] = b"\x03\x00"
    header[28:30] = b"\xfe\xff"
    header[30:32] = b"\x09\x00"
    header[32:34] = b"\x06\x00"
    header[44:48] = struct.pack("<I", 1)
    header[48:52] = struct.pack("<I", 1)
    header[56:60] = struct.pack("<I", 4096)
    header[60:64] = struct.pack("<I", 0xFFFFFFFE)
    header[68:72] = struct.pack("<I", 0xFFFFFFFE)
    header[76:80] = struct.pack("<I", 0)
    for i in range(80, 512, 4):
        header[i : i + 4] = struct.pack("<I", 0xFFFFFFFF)

    fat = bytearray(512)
    fat[0:4] = struct.pack("<I", 0xFFFFFFFD)
    fat[4:8] = struct.pack("<I", 0xFFFFFFFE)
    for s in range(num_sectors):
        sect_idx = 2 + s
        next_val = (sect_idx + 1) if s < num_sectors - 1 else 0xFFFFFFFE
        fat[sect_idx * 4 : (sect_idx + 1) * 4] = struct.pack("<I", next_val)
    for i in range((2 + num_sectors) * 4, 512, 4):
        fat[i : i + 4] = struct.pack("<I", 0xFFFFFFFF)

    dir_sect = bytearray(512)
    root_name = "Root Entry\0".encode("utf-16le")
    dir_sect[0 : len(root_name)] = root_name
    dir_sect[64:66] = struct.pack("<H", len(root_name))
    dir_sect[66] = 5
    dir_sect[67] = 1
    dir_sect[68:72] = struct.pack("<I", 0xFFFFFFFF)
    dir_sect[72:76] = struct.pack("<I", 0xFFFFFFFF)
    dir_sect[76:80] = struct.pack("<I", 1)
    dir_sect[116:120] = struct.pack("<I", 0xFFFFFFFE)

    stream_name = "WordDocument\0".encode("utf-16le")
    e1 = 128
    dir_sect[e1 : e1 + len(stream_name)] = stream_name
    dir_sect[e1 + 64 : e1 + 66] = struct.pack("<H", len(stream_name))
    dir_sect[e1 + 66] = 2
    dir_sect[e1 + 67] = 1
    dir_sect[e1 + 68 : e1 + 72] = struct.pack("<I", 0xFFFFFFFF)
    dir_sect[e1 + 72 : e1 + 76] = struct.pack("<I", 0xFFFFFFFF)
    dir_sect[e1 + 76 : e1 + 80] = struct.pack("<I", 0xFFFFFFFF)
    dir_sect[e1 + 116 : e1 + 120] = struct.pack("<I", 2)
    dir_sect[e1 + 120 : e1 + 124] = struct.pack("<I", len(content))

    return bytes(header + fat + dir_sect + content_padded)


@pytest.mark.asyncio
async def test_legacy_doc_extractor(temp_dir: Path) -> None:
    doc_path = temp_dir / "legacy.doc"
    raw_doc_bytes = create_synthetic_doc_bytes("Extracted legacy Word document content.\n\n")
    doc_path.write_bytes(raw_doc_bytes)

    extractor = LegacyDocExtractor()
    canonical_doc = await extractor.extract_document(doc_path, "legacy.doc")

    assert canonical_doc.detected_format == "doc"
    assert canonical_doc.extraction_status in (
        ExtractionStatus.COMPLETED,
        ExtractionStatus.COMPLETED_WITH_WARNINGS,
    )
    assert len(canonical_doc.blocks) >= 1
    assert any("Extracted legacy Word document" in b.text for b in canonical_doc.blocks)


# ==============================================================================
# 4. Plain Text Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_plain_text_extractor_utf8_and_bom(temp_dir: Path) -> None:
    # 1. UTF-8 with BOM
    txt_bom_path = temp_dir / "utf8_bom.txt"
    txt_bom_path.write_bytes(b"\xef\xbb\xbfDocuMind Plain Text\n\nParagraph two with details.")

    extractor = PlainTextExtractor()
    canonical_doc = await extractor.extract_document(txt_bom_path, "utf8_bom.txt")

    assert canonical_doc.detected_format == "txt"
    assert canonical_doc.metadata["encoding"] == "utf-8-sig"
    assert len(canonical_doc.blocks) == 2
    assert canonical_doc.blocks[0].text == "DocuMind Plain Text"
    assert canonical_doc.blocks[1].text == "Paragraph two with details."

    # 2. Latin-1 / CP1252 with special characters
    txt_latin_path = temp_dir / "latin1.txt"
    txt_latin_path.write_bytes("Café Münsterländer Überprüfung".encode("iso-8859-1"))

    doc_latin = await extractor.extract_document(txt_latin_path, "latin1.txt")
    assert doc_latin.detected_format == "txt"
    assert "Münsterländer" in doc_latin.blocks[0].text


# ==============================================================================
# 5. Markdown Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_markdown_extractor(temp_dir: Path) -> None:
    md_path = temp_dir / "document.md"
    content = """---
title: Project Documentation
version: 3.0.0
author: Antigravity Team
---

# Main Overview

This is the introductory paragraph for DocuMind extraction.

## Features

- Multi-format ingestion
- Canonical document schema
- GFM Markdown generation

```python
def extract_file(path: str) -> dict:
    return {"status": "ok"}
```

| Format | Engine |
| --- | --- |
| PDF | PyMuPDF |
| DOCX | python-docx |
"""
    md_path.write_text(content, encoding="utf-8")

    extractor = MarkdownExtractor()
    canonical_doc = await extractor.extract_document(md_path, "document.md")

    assert canonical_doc.detected_format == "md"
    assert canonical_doc.metadata.get("title") == "Project Documentation"
    assert canonical_doc.metadata.get("author") == "Antigravity Team"

    # Verify block semantics
    types = [b.block_type for b in canonical_doc.blocks]
    assert BlockType.HEADING in types
    assert BlockType.PARAGRAPH in types
    assert BlockType.LIST_ITEM in types
    assert BlockType.CODE in types
    assert BlockType.TABLE in types

    code_block = next(b for b in canonical_doc.blocks if b.block_type == BlockType.CODE)
    assert "def extract_file" in code_block.text
    assert code_block.metadata.get("language") == "python"


# ==============================================================================
# 6. RTF Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_rtf_extractor(temp_dir: Path) -> None:
    rtf_path = temp_dir / "sample.rtf"
    rtf_bytes = (
        b"{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Arial;}}\n"
        b"\\f0\\fs28 Document Title\\par\\par\n"
        b"\\f0\\fs20 This is a rich text paragraph containing bold \\b formatting\\b0.\\par\n"
        b"}"
    )
    rtf_path.write_bytes(rtf_bytes)

    extractor = RTFExtractor()
    canonical_doc = await extractor.extract_document(rtf_path, "sample.rtf")

    assert canonical_doc.detected_format == "rtf"
    assert len(canonical_doc.blocks) >= 2
    assert "Document Title" in canonical_doc.blocks[0].text
    assert "formatting" in canonical_doc.blocks[1].text


# ==============================================================================
# 7. ODT Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_odt_extractor(temp_dir: Path) -> None:
    odt_path = temp_dir / "document.odt"

    content_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                         xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
                         xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">
  <office:body>
    <office:text>
      <text:h text:outline-level="1">OpenDocument Heading</text:h>
      <text:p>Body text in open document format.</text:p>
      <text:list>
        <text:list-item><text:p>First item</text:p></text:list-item>
        <text:list-item><text:p>Second item</text:p></text:list-item>
      </text:list>
      <table:table table:name="Table1">
        <table:table-row>
          <table:table-cell><text:p>Header1</text:p></table:table-cell>
          <table:table-cell><text:p>Header2</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell><text:p>Data1</text:p></table:table-cell>
          <table:table-cell><text:p>Data2</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:text>
  </office:body>
</office:document-content>
"""
    meta_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                      xmlns:dc="http://purl.org/dc/elements/1.1/"
                      xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0">
  <office:meta>
    <dc:title>ODF Specification</dc:title>
    <dc:creator>OASIS Committee</dc:creator>
  </office:meta>
</office:document-meta>
"""
    with zipfile.ZipFile(odt_path, "w") as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        zf.writestr("content.xml", content_xml)
        zf.writestr("meta.xml", meta_xml)

    extractor = ODTExtractor()
    canonical_doc = await extractor.extract_document(odt_path, "document.odt")

    assert canonical_doc.detected_format == "odt"
    assert canonical_doc.metadata["title"] == "ODF Specification"
    assert canonical_doc.metadata["author"] == "OASIS Committee"

    headings = [b for b in canonical_doc.blocks if b.block_type == BlockType.HEADING]
    assert len(headings) == 1
    assert headings[0].text == "OpenDocument Heading"

    tables = [b for b in canonical_doc.blocks if b.block_type == BlockType.TABLE]
    assert len(tables) == 1
    assert tables[0].metadata["table_grid"] == [["Header1", "Header2"], ["Data1", "Data2"]]


# ==============================================================================
# 8. EPUB Extractor Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_epub_extractor(temp_dir: Path) -> None:
    epub_path = temp_dir / "sample.epub"

    book = epub.EpubBook()
    book.set_identifier("documind-12345")
    book.set_title("DocuMind Guidebook")
    book.set_language("en")
    book.add_author("Antigravity Author")

    # Chapter 1
    c1 = epub.EpubHtml(title="Introduction", file_name="chap_01.xhtml", lang="en")
    c1.content = "<h1>Chapter One</h1><p>Welcome to the universal file extraction guide.</p>"
    book.add_item(c1)

    # Chapter 2 with table and list
    c2 = epub.EpubHtml(title="Architecture", file_name="chap_02.xhtml", lang="en")
    c2.content = (
        "<h2>Engine Design</h2>"
        "<p>Key architecture features:</p>"
        "<ul><li>Zero hallucinations</li><li>Preserved reading order</li></ul>"
        "<table><tr><th>Format</th><th>Status</th></tr><tr><td>PDF</td><td>Supported</td></tr></table>"
    )
    book.add_item(c2)

    book.toc = (c1, c2)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", c1, c2]

    epub.write_epub(str(epub_path), book)

    extractor = EPUBExtractor()
    canonical_doc = await extractor.extract_document(epub_path, "sample.epub")

    assert canonical_doc.detected_format == "epub"
    assert canonical_doc.metadata["title"] == "DocuMind Guidebook"
    assert canonical_doc.metadata["author"] == "Antigravity Author"
    assert canonical_doc.page_count >= 2

    # Verify extracted block contents
    texts = [b.text for b in canonical_doc.blocks]
    assert any("Chapter One" in t for t in texts)
    assert any("Engine Design" in t for t in texts)
    assert any("Zero hallucinations" in t for t in texts)


# ==============================================================================
# 9. Output Generators Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_generators(temp_dir: Path) -> None:
    md_path = temp_dir / "gen_test.md"
    md_path.write_text("# Title\n\nParagraph text.\n\n| A | B |\n|---|---|\n| 1 | 2 |")

    extractor = MarkdownExtractor()
    doc = await extractor.extract_document(md_path, "gen_test.md")

    # 1. JSON Generator
    json_str = JSONGenerator.generate(doc)
    assert '"document_id"' in json_str
    assert '"blocks"' in json_str

    # 2. Markdown Generator
    markdown_str = MarkdownGenerator.generate(doc)
    assert "# Title" in markdown_str
    assert "Paragraph text." in markdown_str
    assert "| A | B |" in markdown_str

    # 3. Manifest Generator
    manifest = ManifestGenerator.generate(
        document=doc,
        execution_time_seconds=0.045,
        output_files={"json": "path/doc.json", "markdown": "path/doc.md"},
    )
    assert manifest.extracted_block_count == len(doc.blocks)
    assert manifest.execution_time_seconds == 0.045
    assert manifest.overall_confidence == 1.0


# ==============================================================================
# 10. Pipeline Supported Formats Coverage
# ==============================================================================


def test_pipeline_covers_all_phase3_formats() -> None:
    supported = extraction_pipeline.list_supported_formats()
    required = ["pdf", "docx", "doc", "txt", "md", "rtf", "odt", "epub"]
    for req in required:
        assert req in supported, f"Format '{req}' missing from extraction pipeline"


# ==============================================================================
# 11. Multi-Column Reading Order Sorting Test
# ==============================================================================


def test_pdf_multi_column_reading_order_sorting() -> None:
    extractor = PDFExtractor()
    page_width = 600.0

    # Blocks:
    # 1. Spanning Title at top: y=20..50, x=50..550 (width=500 > 60% of 600)
    # 2. Left column para 1: y=80..120, x=50..250
    # 3. Left column para 2: y=130..180, x=50..250
    # 4. Right column para 1: y=80..120, x=350..550
    # 5. Right column para 2: y=130..180, x=350..550
    # 6. Spanning footer at bottom: y=500..530, x=50..550

    title = [50.0, 20.0, 550.0, 50.0, "Title Block", 0, 0]
    left1 = [50.0, 80.0, 250.0, 120.0, "Left Column 1", 0, 0]
    left2 = [50.0, 130.0, 250.0, 180.0, "Left Column 2", 0, 0]
    right1 = [350.0, 80.0, 550.0, 120.0, "Right Column 1", 0, 0]
    right2 = [350.0, 130.0, 550.0, 180.0, "Right Column 2", 0, 0]
    footer = [50.0, 500.0, 550.0, 530.0, "Footer Block", 0, 0]

    # Scrambled input order
    input_blocks = [right1, left2, footer, title, right2, left1]
    sorted_blocks = extractor._sort_blocks_reading_order(input_blocks, page_width=page_width)

    # In multi-column reading order:
    # Expected: Title -> Left 1 -> Left 2 -> Right 1 -> Right 2 -> Footer
    sorted_texts = [b[4] for b in sorted_blocks]
    assert sorted_texts == [
        "Title Block",
        "Left Column 1",
        "Left Column 2",
        "Right Column 1",
        "Right Column 2",
        "Footer Block",
    ]
