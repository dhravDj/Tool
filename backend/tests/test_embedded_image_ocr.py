import io
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw

from app.modules.converters.adapters.document_adapter import DocumentAdapter
from app.modules.converters.writers.markdown_writer import MarkdownWriter
from app.modules.converters.writers.txt_writer import TxtWriter
from app.modules.extraction.adapters.pdf import PDFExtractor


@pytest.mark.asyncio
async def test_pdf_embedded_image_ocr_extraction(tmp_path: Path):
    """Verify that images placed inside PDF pages are detected, scanned via OCR, and transcribed into text."""
    # 1. Generate test image with clear text
    img = Image.new("RGB", (350, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((15, 35), "EMBEDDED_DIAGRAM_VALUE_4455", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # 2. Build PDF document with native text and embedded image
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), "Chapter 1: The Introduction", fontsize=14)
    page.insert_image(pymupdf.Rect(50, 120, 400, 220), stream=img_bytes)
    page.insert_text((50, 300), "Chapter 1: Native Text Conclusion", fontsize=12)

    pdf_path = tmp_path / "mixed_embedded.pdf"
    doc.save(str(pdf_path))
    doc.close()

    # 3. Extract and convert
    extractor = PDFExtractor()
    canon_doc = await extractor.extract_document(
        pdf_path, "mixed_embedded.pdf", {"ocr_enabled": True}
    )
    univ = DocumentAdapter.adapt(canon_doc)
    md_content = MarkdownWriter.write(univ)
    txt_content = TxtWriter.write(univ)

    # 4. Assert both native and OCR embedded text appear
    assert "Chapter 1: The Introduction" in md_content
    assert "4455" in md_content or "EMBEDDED" in md_content
    assert "Native Text Conclusion" in md_content

    assert "Chapter 1: The Introduction" in txt_content
    assert "4455" in txt_content or "EMBEDDED" in txt_content
    assert "Native Text Conclusion" in txt_content


@pytest.mark.asyncio
async def test_large_pdf_full_conversion_to_end(tmp_path: Path):
    """Verify that multi-page large documents are fully converted to the very last page without truncation."""
    doc = pymupdf.open()
    total_pages = 25
    for p_idx in range(total_pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), f"Document Section On Page {p_idx + 1}", fontsize=12)
        page.insert_text(
            (50, 120),
            f"Body text content for page {p_idx + 1} with detailed paragraphs.",
            fontsize=10,
        )

    # Insert unique marker on the very last page
    page_last = doc[total_pages - 1]
    page_last.insert_text((50, 200), "FINAL_PAGE_CONCLUSION_SIGN_OFF_VERIFIED", fontsize=11)

    pdf_path = tmp_path / "large_document.pdf"
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    canon_doc = await extractor.extract_document(
        pdf_path, "large_document.pdf", {"ocr_enabled": False}
    )
    univ = DocumentAdapter.adapt(canon_doc)
    md_content = MarkdownWriter.write(univ)
    txt_content = TxtWriter.write(univ)

    # Verify beginning, middle, and absolute final page are present
    assert "Document Section On Page 1" in md_content
    assert "Document Section On Page 12" in md_content
    assert "FINAL_PAGE_CONCLUSION_SIGN_OFF_VERIFIED" in md_content
    assert "FINAL_PAGE_CONCLUSION_SIGN_OFF_VERIFIED" in txt_content
