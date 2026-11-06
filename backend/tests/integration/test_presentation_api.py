"""Integration tests for Presentation Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "presentations"


@pytest.mark.asyncio
async def test_presentation_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/presentation-intelligence/capabilities."""
    res = await async_client.get("/api/v1/presentation-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["pptx", "ppt", "odp"]:
        assert fmt in data["supported_formats"]

    assert data["native_pptx_supported"] is True
    assert data["native_odp_supported"] is True
    assert data["legacy_ppt_supported"] is True
    assert data["chart_extraction_supported"] is True
    assert data["speaker_notes_supported"] is True


@pytest.mark.asyncio
async def test_presentation_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete presentation lifecycle: upload -> analyze -> inspect -> export."""
    # 1. Read test fixture
    fixture_path = FIXTURES_DIR / "pptx_tables.pptx"
    assert fixture_path.exists(), "Fixture pptx_tables.pptx must exist"

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    # 2. Upload and persist file
    files = {
        "file": (
            "quarterly_tables.pptx",
            io.BytesIO(file_bytes),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 3. Trigger Presentation Analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-presentation")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["slide_count"] >= 1
    assert "json" in manifest["artifacts"]
    assert "markdown" in manifest["artifacts"]
    assert "text" in manifest["artifacts"]

    # 4. Retrieve Presentation Analysis Record Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis")
    assert overview_res.status_code == 200
    ov_data = overview_res.json()["data"]
    assert ov_data["file_id"] == file_id
    assert ov_data["format"] == "pptx"
    assert ov_data["slide_count"] >= 1
    assert ov_data["has_tables"] is True

    # 5. Retrieve Canonical Document Result
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert len(doc_data["slides"]) >= 1
    assert len(doc_data["tables"]) >= 1

    # 6. Retrieve Slides List
    slides_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/slides")
    assert slides_res.status_code == 200
    slides_list = slides_res.json()["data"]
    assert len(slides_list) >= 1
    first_slide_id = slides_list[0]["slide_id"]

    # 7. Retrieve Slide Detail
    slide_detail_res = await async_client.get(
        f"/api/v1/files/{file_id}/presentation-analysis/slides/{first_slide_id}"
    )
    assert slide_detail_res.status_code == 200
    slide_detail = slide_detail_res.json()["data"]
    assert slide_detail["slide_id"] == first_slide_id
    assert len(slide_detail["tables"]) >= 1

    # 8. Retrieve Presentation Summary
    summary_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]
    assert summary_data["slide_count"] >= 1
    assert summary_data["tables_count"] >= 1

    # 9. Test Artifact Export (Markdown, JSON, Text)
    md_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/export/markdown")
    assert md_res.status_code == 200
    assert b"Quarterly Revenue Summary" in md_res.content

    json_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/export/json")
    assert json_res.status_code == 200
    assert b"document_id" in json_res.content

    txt_res = await async_client.get(f"/api/v1/files/{file_id}/presentation-analysis/download?format=text")
    assert txt_res.status_code == 200
    assert b"SLIDE 1" in txt_res.content
