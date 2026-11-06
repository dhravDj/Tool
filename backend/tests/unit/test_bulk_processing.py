"""Unit tests for Phase 12: Large-Scale Bulk Processing & Scalability Engine."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProcessingJobRecord, User
from app.modules.bulk_processing.capacity.system_monitor import system_monitor
from app.modules.bulk_processing.dedup.deduplicator import deduplication_engine
from app.modules.bulk_processing.orchestrator.batch_manager import batch_manager
from app.modules.bulk_processing.queue.priority_queue import (
    PriorityTaskQueue,
    get_queue_tier,
)
from app.modules.bulk_processing.schemas.batch import BatchCreateRequest, ProcessingPolicy


def test_priority_tier_mapping() -> None:
    """Verify numeric priorities (1-100) map to expected queue tiers."""
    assert get_queue_tier(90) == "interactive"
    assert get_queue_tier(80) == "interactive"
    assert get_queue_tier(79) == "normal"
    assert get_queue_tier(50) == "normal"
    assert get_queue_tier(49) == "bulk"
    assert get_queue_tier(30) == "bulk"
    assert get_queue_tier(20) == "maintenance"
    assert get_queue_tier(5) == "maintenance"


@pytest.mark.asyncio
async def test_priority_queue_tier_ordering() -> None:
    """Verify tasks are popped in strict priority order (interactive > normal > bulk > maintenance)."""
    q = PriorityTaskQueue()
    await q.clear()

    # Enqueue in reverse priority
    await q.enqueue("task_maint", {"step": 1}, priority=10)
    await q.enqueue("task_bulk", {"step": 2}, priority=30)
    await q.enqueue("task_normal", {"step": 3}, priority=50)
    await q.enqueue("task_inter", {"step": 4}, priority=90)

    # Pop order must be interactive first, then normal, bulk, maintenance
    m1 = await q.pop()
    assert m1 is not None and m1.task_name == "task_inter"
    await q.ack(m1.id)

    m2 = await q.pop()
    assert m2 is not None and m2.task_name == "task_normal"
    await q.ack(m2.id)

    m3 = await q.pop()
    assert m3 is not None and m3.task_name == "task_bulk"
    await q.ack(m3.id)

    m4 = await q.pop()
    assert m4 is not None and m4.task_name == "task_maint"
    await q.ack(m4.id)

    # Queue should now be empty
    m5 = await q.pop()
    assert m5 is None


@pytest.mark.asyncio
async def test_priority_queue_idempotency() -> None:
    """Verify identical idempotency key prevents duplicate enqueue and returns existing task ID."""
    q = PriorityTaskQueue()
    await q.clear()
    key = f"idemp_{uuid.uuid4().hex}"

    task_id1 = await q.enqueue("task_one", {"data": 123}, priority=50, idempotency_key=key)
    task_id2 = await q.enqueue("task_one", {"data": 123}, priority=50, idempotency_key=key)

    assert task_id1 == task_id2

    # Should only pop once
    m1 = await q.pop()
    assert m1 is not None and m1.id == task_id1
    await q.ack(m1.id)

    m2 = await q.pop()
    assert m2 is None


@pytest.mark.asyncio
async def test_priority_queue_cancellation() -> None:
    """Verify cancelled tasks are discarded and not returned on pop."""
    q = PriorityTaskQueue()
    await q.clear()

    t1 = await q.enqueue("to_cancel", {"step": 1}, priority=50)
    t2 = await q.enqueue("to_keep", {"step": 2}, priority=50)

    await q.cancel_task(t1)

    popped = await q.pop()
    assert popped is not None
    assert popped.id == t2
    assert popped.task_name == "to_keep"
    await q.ack(popped.id)


def test_priority_queue_exponential_backoff() -> None:
    """Verify exponential backoff calculation with jitter adheres to bounds."""
    q = PriorityTaskQueue()

    d1 = q.compute_backoff_delay(attempt=1, base_delay=1.0, max_delay=60.0, jitter=False)
    d2 = q.compute_backoff_delay(attempt=2, base_delay=1.0, max_delay=60.0, jitter=False)
    d3 = q.compute_backoff_delay(attempt=3, base_delay=1.0, max_delay=60.0, jitter=False)

    assert d1 == 1.0  # 1.0 * (2^0)
    assert d2 == 2.0  # 1.0 * (2^1)
    assert d3 == 4.0  # 1.0 * (2^2)

    # Clamping at max_delay
    d_huge = q.compute_backoff_delay(attempt=20, base_delay=1.0, max_delay=60.0, jitter=False)
    assert d_huge == 60.0

    # With jitter
    d_jit = q.compute_backoff_delay(attempt=3, base_delay=1.0, max_delay=60.0, jitter=True)
    assert 2.0 <= d_jit <= 4.0


@pytest.mark.asyncio
async def test_deduplicator_tenant_isolation(db_session: AsyncSession) -> None:
    """Verify duplicate detection respects strict multi-tenant user boundaries."""
    u1 = User(
        email=f"user1_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
    )
    u2 = User(
        email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
    )
    db_session.add_all([u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)
    await db_session.refresh(u2)

    test_sha256 = f"hash_{uuid.uuid4().hex}"
    test_size = 2048

    # First upload by u1 -> new
    res1 = await deduplication_engine.check_duplicate(
        session=db_session,
        sha256_hash=test_sha256,
        file_size=test_size,
        owner_id=u1.id,
    )
    assert res1.is_duplicate is False
    assert res1.dedup_decision == "new"

    # Register record for u1
    from app.infrastructure.database.models import FileRecord
    f1 = FileRecord(
        original_filename="doc1.pdf",
        stored_filename=f"doc1_{uuid.uuid4().hex[:8]}.pdf",
        extension="pdf",
        storage_path=f"storage/{test_sha256}",
        file_size=test_size,
        sha256=test_sha256,
        status="processed",
        owner_id=u1.id,
    )
    db_session.add(f1)
    await db_session.commit()

    # Second check by u1 -> duplicate!
    res2 = await deduplication_engine.check_duplicate(
        session=db_session,
        sha256_hash=test_sha256,
        file_size=test_size,
        owner_id=u1.id,
    )
    assert res2.is_duplicate is True
    assert res2.existing_file_id == f1.id
    assert res2.dedup_decision == "duplicate"

    # Check by u2 for SAME hash -> new! (tenant isolation)
    res3 = await deduplication_engine.check_duplicate(
        session=db_session,
        sha256_hash=test_sha256,
        file_size=test_size,
        owner_id=u2.id,
    )
    assert res3.is_duplicate is False
    assert res3.dedup_decision == "new"


@pytest.mark.asyncio
async def test_batch_manager_lifecycle(db_session: AsyncSession) -> None:
    """Verify batch creation, bounded chunked file addition, and lifecycle status changes."""
    # 1. Create batch
    req = BatchCreateRequest(
        name="Test Ingestion Batch",
        policy=ProcessingPolicy(priority=50, max_parallel_workers=4),
    )
    batch_resp = await batch_manager.create_batch(db_session, req)
    assert batch_resp.name == "Test Ingestion Batch"
    assert batch_resp.status == "pending"
    b_id = uuid.UUID(batch_resp.id)

    # 2. Add 120 files in bulk (crosses 100-chunk threshold)
    files_data = [
        {
            "filename": f"sample_{i}.txt",
            "file_size": 1000 + i,
            "sha256": f"dummy_sha_{i}",
            "file_id": uuid.uuid4(),
            "status": "accepted",
            "dedup_decision": "new",
        }
        for i in range(120)
    ]
    updated_batch = await batch_manager.add_files_to_batch(db_session, b_id, files_data)
    assert updated_batch.total_files == 120
    assert updated_batch.accepted_files == 120

    # 3. Start batch
    started_batch = await batch_manager.start_batch(db_session, b_id)
    assert started_batch.status == "processing"

    # 4. Pause batch
    paused_batch = await batch_manager.pause_batch(db_session, b_id)
    assert paused_batch.status == "paused"

    # 5. Cancel batch
    cancelled_batch = await batch_manager.cancel_batch(db_session, b_id)
    assert cancelled_batch.status == "cancelled"


@pytest.mark.asyncio
async def test_batch_progress_calculation(db_session: AsyncSession) -> None:
    """Verify accurate work-weighted progress computation for jobs in a batch."""
    req = BatchCreateRequest(name="Progress Calculation Batch")
    batch_resp = await batch_manager.create_batch(db_session, req)
    b_id = uuid.UUID(batch_resp.id)

    # Add 2 jobs: 1 completed (100%), 1 half-done (50%) -> overall = 75.0%
    fid1 = uuid.uuid4()
    fid2 = uuid.uuid4()
    files_data = [
        {"filename": "f1.pdf", "file_size": 100, "file_id": fid1, "status": "accepted"},
        {"filename": "f2.pdf", "file_size": 200, "file_id": fid2, "status": "accepted"},
    ]
    await batch_manager.add_files_to_batch(db_session, b_id, files_data)

    # Start to generate jobs
    await batch_manager.start_batch(db_session, b_id)

    # Simulate worker updates to jobs
    from sqlalchemy import select
    res = await db_session.execute(
        select(ProcessingJobRecord).where(ProcessingJobRecord.batch_id == b_id)
    )
    jobs = res.scalars().all()
    assert len(jobs) == 2

    jobs[0].status = "completed"
    jobs[0].progress = 100.0

    jobs[1].status = "processing"
    jobs[1].progress = 50.0

    await db_session.commit()

    # Get progress
    progress = await batch_manager.get_batch_progress(db_session, b_id)
    assert progress.total_files == 2
    assert progress.completed_files == 1
    assert progress.processing_files == 1
    assert progress.overall_progress == 75.0


@pytest.mark.asyncio
async def test_system_monitor_metrics() -> None:
    """Verify system monitor returns valid hardware capacity, resource usage, and queue telemetry."""
    cap = await system_monitor.get_system_capacity()
    assert cap.max_parallel_cpu_workers >= 1
    assert cap.max_concurrent_gpu_slots >= 1
    assert cap.submission_capacity_files_per_sec > 0
    assert isinstance(cap.is_under_backpressure, bool)

    resources = await system_monitor.get_resource_usage()
    assert resources.cpu.get("logical_cores", 0) >= 1
    assert resources.memory.get("total_ram_mb", 0) > 0
    assert resources.storage.get("total_gb", 0) > 0
