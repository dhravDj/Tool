"""Integration tests for Structured Data Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "structured"


@pytest.mark.asyncio
async def test_structured_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/structured-data-intelligence/capabilities."""
    res = await async_client.get("/api/v1/structured-data-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["json", "xml", "yaml", "toml", "parquet"]:
        assert fmt in data["supported_formats"]
    assert "parquet_columnar_profiling_zero_dataframe" in data["features"]


@pytest.mark.asyncio
async def test_structured_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete structured data lifecycle: upload -> analyze -> overview -> result -> schema -> profile -> records -> export."""
    fixture_path = FIXTURES_DIR / "valid.parquet"
    file_bytes = fixture_path.read_bytes()

    # 1. Upload and persist file
    files = {
        "file": (
            "valid.parquet",
            io.BytesIO(file_bytes),
            "application/x-parquet",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger Structured Data Analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-structured-data")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["format"] == "parquet"
    assert manifest["total_rows"] == 5

    # 3. Retrieve Structured Analysis Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert overview_data["status"] == "completed"
    assert overview_data["format"] == "parquet"
    assert overview_data["record_count"] == 5
    assert overview_data["field_count"] == 4

    # 4. Retrieve Full Canonical StructuredDataDocument Result
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert doc_data["format"] == "parquet"
    assert len(doc_data["records"]) == 5

    # 5. Retrieve Schema
    schema_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis/schema")
    assert schema_res.status_code == 200
    schema_data = schema_res.json()["data"]
    assert "fields" in schema_data or "columns" in schema_data or "type" in schema_data

    # 6. Retrieve Profile
    prof_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis/profile")
    assert prof_res.status_code == 200
    prof_data = prof_res.json()["data"]
    assert prof_data["total_rows"] == 5
    assert len(prof_data["column_profiles"]) == 4

    # 7. Retrieve Sample Records
    rec_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis/records")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()["data"]
    assert len(rec_data["records"]) == 5

    # 8. Exports (JSON, Markdown, CSV)
    for exp_fmt in ["json", "markdown", "csv"]:
        exp_res = await async_client.get(f"/api/v1/files/{file_id}/structured-data-analysis/export/{exp_fmt}")
        assert exp_res.status_code == 200
        assert len(exp_res.text) > 30
