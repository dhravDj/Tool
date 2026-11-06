"""Integration tests for Archive Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "archives"


@pytest.mark.asyncio
async def test_archive_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/archive-intelligence/capabilities."""
    res = await async_client.get("/api/v1/archive-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["zip", "7z", "tar", "tar.gz", "tgz", "gz", "tar.bz2", "tbz2", "tar.xz", "txz"]:
        assert fmt in data["supported_formats"]
    assert "archive_bomb_protection" in data["features"]
    assert "path_traversal_defense" in data["features"]
    assert data["max_nesting_depth"] == 5


@pytest.mark.asyncio
async def test_archive_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete archive inspection, tree, entries, extraction, security report, and exports."""
    fixture_path = FIXTURES_DIR / "valid_mixed.zip"
    file_bytes = fixture_path.read_bytes()

    # 1. Upload and persist file
    files = {
        "file": (
            "valid_mixed.zip",
            io.BytesIO(file_bytes),
            "application/zip",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger Archive Inspection (Mode A: inspect_only)
    analyze_res = await async_client.post(
        f"/api/v1/files/{file_id}/analyze-archive",
        json={"mode": "inspect_only"},
    )
    assert analyze_res.status_code == 200
    doc = analyze_res.json()["data"]
    assert doc["source_file_id"] == file_id
    assert doc["archive_format"] == "zip"
    assert doc["processing_mode"] == "inspect_only"
    assert doc["total_entry_count"] == 6

    # 3. Get Archive Analysis Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert overview_data["status"] == "completed"
    assert overview_data["file_count"] == 6

    # 4. Get Result and Summary
    res_doc = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/result")
    assert res_doc.status_code == 200
    assert res_doc.json()["data"]["archive_format"] == "zip"

    sum_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/summary")
    assert sum_res.status_code == 200
    assert sum_res.json()["data"]["entry_count"] == 6

    # 5. List Entries
    entries_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/entries")
    assert entries_res.status_code == 200
    entries_list = entries_res.json()["data"]
    assert len(entries_list) == 6
    target_entry_id = entries_list[0]["entry_id"]

    # 6. Get Single Entry
    single_res = await async_client.get(
        f"/api/v1/files/{file_id}/archive-analysis/entries/{target_entry_id}"
    )
    assert single_res.status_code == 200
    assert single_res.json()["data"]["entry_id"] == target_entry_id

    # 7. Get Tree
    tree_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/tree")
    assert tree_res.status_code == 200
    assert "children" in tree_res.json()["data"]

    # 8. Trigger Safe Extraction (Mode B: extract_only)
    extract_res = await async_client.post(
        f"/api/v1/files/{file_id}/archive-analysis/extract",
        json={"mode": "extract_only"},
    )
    assert extract_res.status_code == 200
    ext_doc = extract_res.json()["data"]
    assert len(ext_doc["extracted_files"]) == 6

    # 9. Get Extraction Status & Children
    status_res = await async_client.get(
        f"/api/v1/files/{file_id}/archive-analysis/extraction-status"
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] in ("completed", "partial")

    children_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/children")
    assert children_res.status_code == 200
    assert len(children_res.json()["data"]) >= 6

    # 10. Get Security Report
    sec_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/security-report")
    assert sec_res.status_code == 200
    assert "safety_summary" in sec_res.json()["data"]

    # 11. Test Export Endpoints
    for fmt in [
        "json",
        "markdown",
        "text",
        "manifest",
        "tree",
        "extraction_report",
        "security_report",
        "child_manifest",
    ]:
        exp_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/export/{fmt}")
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 0


@pytest.mark.asyncio
async def test_nested_archive_and_downstream_routing(async_client: AsyncClient) -> None:
    """Test recursive nested archive extraction and routing."""
    fixture_path = FIXTURES_DIR / "nested_archive.zip"
    file_bytes = fixture_path.read_bytes()

    files = {
        "file": (
            "nested_archive.zip",
            io.BytesIO(file_bytes),
            "application/zip",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]

    # Trigger extract and analyze (Mode C)
    analyze_res = await async_client.post(
        f"/api/v1/files/{file_id}/analyze-archive",
        json={"mode": "extract_and_analyze"},
    )
    assert analyze_res.status_code == 200
    doc = analyze_res.json()["data"]
    assert doc["source_file_id"] == file_id
    assert len(doc["extracted_files"]) >= 2

    # Check nested archives list
    nested_res = await async_client.get(f"/api/v1/files/{file_id}/archive-analysis/nested-archives")
    assert nested_res.status_code == 200


@pytest.mark.asyncio
async def test_security_slip_blocking_api(async_client: AsyncClient) -> None:
    """Test API correctly blocks zip slip path traversal and reports security violations."""
    fixture_path = FIXTURES_DIR / "slip_traversal.zip"
    file_bytes = fixture_path.read_bytes()

    files = {
        "file": (
            "slip_traversal.zip",
            io.BytesIO(file_bytes),
            "application/zip",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]

    # Extract
    extract_res = await async_client.post(
        f"/api/v1/files/{file_id}/archive-analysis/extract",
        json={"mode": "extract_only"},
    )
    assert extract_res.status_code == 200
    doc = extract_res.json()["data"]
    assert doc["safety_report"]["path_traversal_blocked"] > 0
    assert len(doc["blocked_entries"]) > 0
