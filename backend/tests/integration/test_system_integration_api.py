"""Integration tests for Phase 13 system integration, dashboard analytics, and file lifecycle endpoints."""

import os
import tempfile
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import FileStatus
from app.infrastructure.database.models import FileRecord, User


@pytest.mark.asyncio
async def test_dashboard_analytics_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test dashboard analytics aggregation endpoint."""
    # Seed a dummy user and file
    u = User(email=f"dash_{uuid.uuid4().hex[:8]}@example.com", password_hash="secret")
    db_session.add(u)
    await db_session.flush()

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Hello DocuMind Dashboard Analytics Test!")
        tmp_path = tmp.name

    try:
        f = FileRecord(
            owner_id=u.id,
            original_filename="sample_dashboard.txt",
            stored_filename=f"sample_{uuid.uuid4().hex}.txt",
            extension="txt",
            detected_mime_type="text/plain",
            file_size=len(b"Hello DocuMind Dashboard Analytics Test!"),
            sha256="d" * 64,
            storage_path=tmp_path,
            status=FileStatus.PROCESSED.value,
            format_category="document",
        )
        db_session.add(f)
        await db_session.commit()

        # Call dashboard-analytics
        response = await async_client.get("/api/v1/system/dashboard-analytics")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]

        # Validate structure
        assert "files_summary" in data
        assert data["files_summary"]["total_files"] >= 1
        assert "ai_summary" in data
        assert "batches_summary" in data
        assert "format_distribution" in data
        assert "status_distribution" in data
        assert "recent_files" in data
        assert len(data["recent_files"]) >= 1
        assert "capacity" in data
        assert "queue_status" in data
        assert "disk_storage" in data

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_file_download_and_delete_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test original file download and secure deletion endpoints."""
    # Create test physical file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 dummy payload")
        tmp_path = tmp.name

    try:
        f = FileRecord(
            original_filename="financial_report.pdf",
            stored_filename=f"fin_{uuid.uuid4().hex}.pdf",
            extension="pdf",
            detected_mime_type="application/pdf",
            file_size=len(b"%PDF-1.4 dummy payload"),
            sha256="a" * 64,
            storage_path=tmp_path,
            status=FileStatus.PROCESSED.value,
            format_category="document",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        # 1. Download
        dl_resp = await async_client.get(f"/api/v1/files/{f.id}/download")
        assert dl_resp.status_code == 200
        assert dl_resp.content == b"%PDF-1.4 dummy payload"
        assert "financial_report.pdf" in dl_resp.headers.get("content-disposition", "")

        # 2. Delete
        del_resp = await async_client.delete(f"/api/v1/files/{f.id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["deleted"] is True
        assert not Path(tmp_path).exists()

        # 3. Confirm 404 after deletion
        get_resp = await async_client.get(f"/api/v1/files/{f.id}")
        assert get_resp.status_code == 404

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_inspect_deduplication_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test the pre-upload deduplication inspection endpoint."""
    test_hash = "f" * 64
    f = FileRecord(
        original_filename="existing_file.docx",
        stored_filename=f"exist_{uuid.uuid4().hex}.docx",
        extension="docx",
        detected_mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size=2048,
        sha256=test_hash,
        storage_path="/tmp/dummy.docx",
        status=FileStatus.PROCESSED.value,
        format_category="document",
    )
    db_session.add(f)
    await db_session.commit()

    # 1. Inspect existing duplicate
    resp_dup = await async_client.post(
        "/api/v1/bulk/inspect-deduplication",
        json={"filename": "upload_candidate.docx", "sha256": test_hash, "file_size": 2048},
    )
    assert resp_dup.status_code == 200
    res_data = resp_dup.json()["data"]
    assert res_data["is_duplicate"] is True
    assert res_data["action"] == "skip"
    assert res_data["existing_filename"] == "existing_file.docx"

    # 2. Inspect brand new file
    resp_new = await async_client.post(
        "/api/v1/bulk/inspect-deduplication",
        json={"filename": "fresh_file.docx", "sha256": "0" * 64, "file_size": 1024},
    )
    assert resp_new.status_code == 200
    new_data = resp_new.json()["data"]
    assert new_data["is_duplicate"] is False
    assert new_data["action"] == "new"
