"""Integration tests for Phase 12 Bulk Processing & Scalability REST API."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_upload_api(async_client: AsyncClient) -> None:
    """Verify streaming multipart bulk upload with automatic batch creation."""
    files = [
        ("files", ("test1.txt", io.BytesIO(b"Hello documind bulk processing 1"), "text/plain")),
        ("files", ("test2.txt", io.BytesIO(b"Hello documind bulk processing 2"), "text/plain")),
    ]
    data = {
        "batch_name": "API Upload Batch",
        "auto_create_batch": "true",
        "auto_start_batch": "false",
    }
    res = await async_client.post("/api/v1/bulk/upload", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    manifest = body["data"]
    assert manifest["total_submitted"] == 2
    assert manifest["total_accepted"] == 2
    assert manifest["total_rejected"] == 0
    assert manifest["batch_id"] is not None
    assert len(manifest["files"]) == 2


@pytest.mark.asyncio
async def test_batch_lifecycle_and_actions_api(async_client: AsyncClient) -> None:
    """Verify batch creation, listing, detail retrieval, pause, resume, cancel, and report generation."""
    # 1. Create batch
    create_payload = {
        "name": "Integration Batch Lifecycle",
        "policy": {
            "priority": 50,
            "max_parallel_workers": 4,
            "continue_on_failure": True,
        },
    }
    create_res = await async_client.post("/api/v1/bulk/batches", json=create_payload)
    assert create_res.status_code == 200
    create_body = create_res.json()
    assert create_body["success"] is True
    batch_data = create_body["data"]
    batch_id = batch_data["id"]
    assert batch_data["name"] == "Integration Batch Lifecycle"
    assert batch_data["status"] == "pending"

    # 2. List batches
    list_res = await async_client.get("/api/v1/bulk/batches")
    assert list_res.status_code == 200
    list_body = list_res.json()
    assert list_body["success"] is True
    assert any(b["id"] == batch_id for b in list_body["data"])

    # 3. Get batch details
    get_res = await async_client.get(f"/api/v1/bulk/batches/{batch_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == batch_id

    # 4. Start batch
    start_res = await async_client.post(f"/api/v1/bulk/batches/{batch_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] in ("processing", "completed")

    # 5. Pause batch
    pause_res = await async_client.post(f"/api/v1/bulk/batches/{batch_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["data"]["status"] == "paused"

    # 6. Resume batch
    resume_res = await async_client.post(f"/api/v1/bulk/batches/{batch_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["data"]["status"] in ("processing", "completed")

    # 7. Cancel batch
    cancel_res = await async_client.post(f"/api/v1/bulk/batches/{batch_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"

    # 8. Retry failed files
    retry_res = await async_client.post(f"/api/v1/bulk/batches/{batch_id}/retry-failed")
    assert retry_res.status_code == 200

    # 9. Get batch progress
    progress_res = await async_client.get(f"/api/v1/bulk/batches/{batch_id}/progress")
    assert progress_res.status_code == 200
    progress_body = progress_res.json()
    assert progress_body["success"] is True
    assert "overall_progress" in progress_body["data"]

    # 10. Get batch report
    report_res = await async_client.get(f"/api/v1/bulk/batches/{batch_id}/report")
    assert report_res.status_code == 200
    report_body = report_res.json()
    assert report_body["success"] is True
    assert report_body["data"]["batch_id"] == batch_id


@pytest.mark.asyncio
async def test_batch_files_listing_api(async_client: AsyncClient) -> None:
    """Verify listing batch files with pagination and status filter."""
    files = [
        ("files", ("file_a.txt", io.BytesIO(b"file content a"), "text/plain")),
        ("files", ("file_b.txt", io.BytesIO(b"file content b"), "text/plain")),
    ]
    upload_res = await async_client.post(
        "/api/v1/bulk/upload",
        files=files,
        data={"batch_name": "Files Listing Batch", "auto_create_batch": "true"},
    )
    assert upload_res.status_code == 200
    b_id = upload_res.json()["data"]["batch_id"]

    # List files
    res = await async_client.get(f"/api/v1/bulk/batches/{b_id}/files")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    items = body["data"]
    assert len(items) == 2
    assert any(f["filename"] == "file_a.txt" for f in items)
    assert any(f["filename"] == "file_b.txt" for f in items)


@pytest.mark.asyncio
async def test_jobs_api_and_queue_status(async_client: AsyncClient) -> None:
    """Verify job querying, queue status, and job cancellation/retry actions."""
    # 1. Check queue status
    q_res = await async_client.get("/api/v1/jobs/queue/status")
    assert q_res.status_code == 200
    q_body = q_res.json()
    assert q_body["success"] is True
    assert "queues" in q_body["data"]
    assert "total_queued" in q_body["data"]

    # 2. List jobs
    jobs_res = await async_client.get("/api/v1/jobs")
    assert jobs_res.status_code == 200
    jobs_body = jobs_res.json()
    assert jobs_body["success"] is True
    assert isinstance(jobs_body["data"], list)

    # 3. If there are jobs, test single job details, cancellation, retry, attempts
    if len(jobs_body["data"]) > 0:
        target_job = jobs_body["data"][0]
        job_id = target_job["id"]

        detail_res = await async_client.get(f"/api/v1/jobs/{job_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["data"]["id"] == job_id

        cancel_job_res = await async_client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancel_job_res.status_code == 200

        retry_job_res = await async_client.post(f"/api/v1/jobs/{job_id}/retry")
        assert retry_job_res.status_code == 200

        attempts_res = await async_client.get(f"/api/v1/jobs/{job_id}/attempts")
        assert attempts_res.status_code == 200
        assert isinstance(attempts_res.json()["data"], list)


@pytest.mark.asyncio
async def test_system_capacity_and_worker_status_api(async_client: AsyncClient) -> None:
    """Verify system capacity, worker status, and host resource telemetry endpoints."""
    # 1. System processing capacity
    cap_res = await async_client.get("/api/v1/system/processing-capacity")
    assert cap_res.status_code == 200
    cap_body = cap_res.json()
    assert cap_body["success"] is True
    cap_data = cap_body["data"]
    assert cap_data["max_parallel_cpu_workers"] >= 1
    assert cap_data["max_concurrent_gpu_slots"] >= 1
    assert "is_under_backpressure" in cap_data

    # 2. Worker status
    workers_res = await async_client.get("/api/v1/system/worker-status")
    assert workers_res.status_code == 200
    workers_body = workers_res.json()
    assert workers_body["success"] is True
    assert isinstance(workers_body["data"], list)

    # 3. Resource usage
    res_res = await async_client.get("/api/v1/system/resource-usage")
    assert res_res.status_code == 200
    res_body = res_res.json()
    assert res_body["success"] is True
    res_data = res_body["data"]
    assert "cpu" in res_data
    assert "memory" in res_data
    assert "storage" in res_data
