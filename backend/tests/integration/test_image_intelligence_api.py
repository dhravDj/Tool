"""Integration tests for Image & Visual Intelligence API endpoints."""

import io
import uuid

import pytest
from httpx import AsyncClient
from PIL import Image


@pytest.mark.asyncio
async def test_image_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/image-intelligence/capabilities."""
    res = await async_client.get("/api/v1/image-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["png", "jpeg", "webp", "tiff", "bmp", "svg"]:
        assert fmt in data["supported_formats"]

    assert "default_vision_engine" in data
    assert data["privacy_gps_scrubbing"] is True
    assert "exif_orientation_correction" in data["preprocessing_steps"]


@pytest.mark.asyncio
async def test_analyze_image_api_end_to_end(async_client: AsyncClient) -> None:
    """Test full image intelligence lifecycle from upload to analysis and VQA query."""
    # 1. Create and upload synthetic PNG image
    img = Image.new("RGB", (320, 240), color=(50, 150, 220))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("cloud_diagram.png", buf, "image/png")}
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger image analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-image")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert "completed" in manifest["status"]
    assert "image_document_json" in manifest["artifacts"]

    # 3. Retrieve analysis status
    status_res = await async_client.get(f"/api/v1/files/{file_id}/image-analysis")
    assert status_res.status_code == 200
    status_data = status_res.json()["data"]
    assert status_data["file_id"] == file_id
    assert status_data["width"] == 320
    assert status_data["height"] == 240
    assert status_data["format"] == "png"

    # 4. Retrieve canonical ImageDocument JSON
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/image-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert doc_data["file_id"] == file_id
    assert doc_data["metadata"]["width"] == 320
    assert "analysis" in doc_data
    assert "caption" in doc_data["analysis"]

    # 5. Ask a grounded question via VQA
    ask_res = await async_client.post(
        f"/api/v1/files/{file_id}/ask-image",
        json={"question": "What colors and scene are shown in this image?"},
    )
    assert ask_res.status_code == 200
    ask_data = ask_res.json()["data"]
    assert ask_data["question"] == "What colors and scene are shown in this image?"
    assert len(ask_data["answer"]) > 10
    assert ask_data["confidence"] > 0.5


@pytest.mark.asyncio
async def test_analyze_non_existent_file_404(async_client: AsyncClient) -> None:
    """Test POST /api/v1/files/{file_id}/analyze-image returns 404 for unknown file."""
    random_id = str(uuid.uuid4())
    res = await async_client.post(f"/api/v1/files/{random_id}/analyze-image")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_image_analysis_status_not_found_404(async_client: AsyncClient) -> None:
    """Test GET /api/v1/files/{file_id}/image-analysis returns 404 when no record exists."""
    random_id = str(uuid.uuid4())
    res = await async_client.get(f"/api/v1/files/{random_id}/image-analysis")
    assert res.status_code == 404
