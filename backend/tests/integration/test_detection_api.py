"""Integration tests for File Detection and Format Registry API endpoints."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_formats_api(async_client: AsyncClient):
    """Test GET /api/v1/formats returns registered formats and supports filtering."""
    # List all formats
    res = await async_client.get("/api/v1/formats")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_formats"] >= 40
    assert len(data["formats"]) >= 40

    # Filter by category
    res_images = await async_client.get("/api/v1/formats?category=image")
    assert res_images.status_code == 200
    img_data = res_images.json()["data"]
    assert img_data["total_formats"] >= 6
    assert all(fmt["category"] == "image" for fmt in img_data["formats"])


@pytest.mark.asyncio
async def test_get_format_by_id_api(async_client: AsyncClient):
    """Test GET /api/v1/formats/{format_id}."""
    # Valid format
    res = await async_client.get("/api/v1/formats/pdf")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["format_id"] == "pdf"
    assert data["canonical_name"] == "Portable Document Format"
    assert "application/pdf" in data["mime_types"]

    # Nonexistent format
    res_404 = await async_client.get("/api/v1/formats/unknown_nonexistent_xyz")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_detection_capabilities_api(async_client: AsyncClient):
    """Test GET /api/v1/system/detection-capabilities."""
    res = await async_client.get("/api/v1/system/detection-capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["engine_version"] == "2.0.0"
    assert data["total_registered_formats"] >= 40
    assert len(data["detection_pipeline_layers"]) == 7


@pytest.mark.asyncio
async def test_detect_single_file_api_persist(async_client: AsyncClient):
    """Test POST /api/v1/files/detect with persistence into library."""
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"

    files = {"file": ("test_logo.png", io.BytesIO(png_content), "image/png")}
    res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["format_id"] == "png"
    assert data["category"] == "image"
    assert data["is_valid"] is True
    assert data["persisted_file_id"] is not None

    # Retrieve persisted detection record
    file_id = data["persisted_file_id"]
    res_get = await async_client.get(f"/api/v1/files/{file_id}/detection")
    assert res_get.status_code == 200
    persisted = res_get.json()["data"]
    assert persisted["format_id"] == "png"
    assert persisted["sha256"] == data["sha256"]


@pytest.mark.asyncio
async def test_detect_extension_mismatch_api(async_client: AsyncClient):
    """Test POST /api/v1/files/detect identifying extension mismatches."""
    # PDF pretending to be a JPG
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
    files = {"file": ("invoice_fake.jpg", io.BytesIO(pdf_content), "image/jpeg")}

    res = await async_client.post("/api/v1/files/detect?persist=false", files=files)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["format_id"] == "pdf"
    assert data["is_mismatch"] is True
    assert data["claimed_extension"] == "jpg"
    assert data["extension"] == "pdf"
    assert any("mismatch" in w.lower() for w in data["warnings"])


@pytest.mark.asyncio
async def test_detect_batch_api(async_client: AsyncClient):
    """Test POST /api/v1/files/detect/batch processing multiple files."""
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    json_data = b'{"status": "ok", "source": "batch"}'
    pdf_data = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

    files = [
        ("files", ("image.png", io.BytesIO(png_data), "image/png")),
        ("files", ("data.json", io.BytesIO(json_data), "application/json")),
        ("files", ("doc.pdf", io.BytesIO(pdf_data), "application/pdf")),
    ]

    res = await async_client.post("/api/v1/files/detect/batch?persist=false", files=files)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_files"] == 3
    assert data["successful_detections"] == 3
    assert len(data["results"]) == 3
