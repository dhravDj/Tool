"""Integration tests for Document Content Extraction API endpoints."""

import io
import uuid

import pymupdf
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_extraction_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/extraction/capabilities."""
    res = await async_client.get("/api/v1/extraction/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verify all 8 formats are listed
    for fmt in ["pdf", "docx", "doc", "txt", "md", "rtf", "odt", "epub"]:
        assert fmt in data["supported_formats"]

    assert "pymupdf_extractor" in data["engines"]
    assert "docx_extractor" in data["engines"]
    assert "legacy_doc_extractor" in data["engines"]


@pytest.mark.asyncio
async def test_extract_markdown_document_end_to_end(async_client: AsyncClient) -> None:
    """Test full extraction flow on a persisted Markdown document."""
    md_content = b"""# DocuMind AI Architecture

Universal file intelligence platform.

## Key Capabilities

- Format detection
- Native text extraction
- Multi-format conversion
"""
    files = {"file": ("architecture.md", io.BytesIO(md_content), "text/markdown")}
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 1. Trigger extraction
    extract_res = await async_client.post(f"/api/v1/files/{file_id}/extract")
    assert extract_res.status_code == 200
    manifest = extract_res.json()["data"]
    assert manifest["document_id"] == file_id
    assert manifest["detected_format"] == "md"
    assert manifest["page_count"] == 1
    assert manifest["extracted_block_count"] >= 3

    # 2. Get extraction status
    status_res = await async_client.get(f"/api/v1/files/{file_id}/extraction")
    assert status_res.status_code == 200
    status_data = status_res.json()["data"]
    assert status_data["file_id"] == file_id
    assert status_data["status"] == "completed"
    assert status_data["detected_format"] == "md"
    assert "canonical_json" in status_data["output_files"]

    # 3. Get canonical document JSON
    canonical_res = await async_client.get(f"/api/v1/files/{file_id}/extraction/result")
    assert canonical_res.status_code == 200
    canonical_doc = canonical_res.json()["data"]
    assert canonical_doc["document_id"] == file_id
    assert len(canonical_doc["pages"]) == 1
    assert len(canonical_doc["blocks"]) >= 3

    # 4. Get generated Markdown
    md_res = await async_client.get(f"/api/v1/files/{file_id}/extraction/markdown")
    assert md_res.status_code == 200
    md_data = md_res.json()["data"]
    assert "DocuMind AI Architecture" in md_data["markdown"]

    # 5. Get raw Markdown stream
    raw_md_res = await async_client.get(f"/api/v1/files/{file_id}/extraction/markdown?raw=true")
    assert raw_md_res.status_code == 200
    assert "text/markdown" in raw_md_res.headers.get("content-type", "")
    assert "DocuMind AI Architecture" in raw_md_res.text

    # 6. Get extraction manifest
    manifest_res = await async_client.get(f"/api/v1/files/{file_id}/extraction/manifest")
    assert manifest_res.status_code == 200
    manifest_data = manifest_res.json()["data"]
    assert manifest_data["document_id"] == file_id
    assert manifest_data["extracted_block_count"] >= 3


@pytest.mark.asyncio
async def test_extract_pdf_document_end_to_end(async_client: AsyncClient) -> None:
    """Test end-to-end extraction on a generated native PDF file."""
    # Create PDF in memory
    doc = pymupdf.open()
    doc.set_metadata({"title": "DocuMind PDF Spec", "author": "QA Team"})
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Chapter 1: Native PDF Extraction", fontsize=16)
    page.insert_text((72, 120), "PyMuPDF delivers high precision coordinate blocks.", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("test_spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]

    # Trigger extraction
    extract_res = await async_client.post(f"/api/v1/files/{file_id}/extract")
    assert extract_res.status_code == 200
    manifest = extract_res.json()["data"]
    assert manifest["detected_format"] == "pdf"
    assert manifest["page_count"] == 1

    # Check canonical result
    canonical_res = await async_client.get(f"/api/v1/files/{file_id}/extraction/result")
    assert canonical_res.status_code == 200
    canonical_data = canonical_res.json()["data"]
    assert canonical_data["metadata"]["title"] == "DocuMind PDF Spec"
    assert canonical_data["metadata"]["author"] == "QA Team"
    assert len(canonical_data["blocks"]) >= 2
    # Verify bounding boxes exist
    assert canonical_data["blocks"][0]["bounding_box"] is not None


@pytest.mark.asyncio
async def test_extract_nonexistent_file_returns_404(async_client: AsyncClient) -> None:
    """Test extracting a non-existent file ID returns 404."""
    random_id = uuid.uuid4()
    res = await async_client.post(f"/api/v1/files/{random_id}/extract")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_extraction_result_nonexistent_returns_404(async_client: AsyncClient) -> None:
    """Test requesting results for a non-extracted file returns 404."""
    random_id = uuid.uuid4()
    res = await async_client.get(f"/api/v1/files/{random_id}/extraction")
    assert res.status_code == 404
