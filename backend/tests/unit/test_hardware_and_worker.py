"""Unit tests for Phase 1 HardwareGovernor and TaskWorker."""

import asyncio
from typing import Any

import pytest

from app.core.hardware import HardwareGovernor
from app.infrastructure.queue.redis import TaskQueue
from app.workers.task_worker import TaskWorker


@pytest.mark.asyncio
async def test_hardware_governor_detection():
    governor = HardwareGovernor(max_cpu_workers=4, max_gpu_slots=1)
    status = governor.detect_hardware()

    assert "cpu" in status
    assert status["cpu"]["active_workers_limit"] == 4
    assert "memory" in status
    assert "accelerator" in status
    assert status["accelerator"]["gpu_concurrency_limit"] == 1


@pytest.mark.asyncio
async def test_hardware_governor_concurrency():
    governor = HardwareGovernor(max_cpu_workers=2, max_gpu_slots=1)
    active = 0
    max_active = 0

    async def worker_job():
        nonlocal active, max_active
        async with governor.cpu_bound_slot():
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.02)
            active -= 1

    await asyncio.gather(*(worker_job() for _ in range(5)))
    assert max_active <= 2


@pytest.mark.asyncio
async def test_task_worker_lifecycle_and_dispatch():
    # In-memory queue testing
    queue = TaskQueue()
    worker = TaskWorker(queue_name="test_worker_queue", poll_interval=0.01)

    processed_tasks = []

    async def sample_handler(payload: dict[str, Any]) -> dict[str, Any]:
        item = payload.get("item")
        processed_tasks.append(item)
        return {"processed": item}

    worker.register_handler("test_job", sample_handler)

    # Enqueue two tasks
    task_id1 = await queue.enqueue("test_job", {"item": "alpha"}, queue_name="test_worker_queue")
    task_id2 = await queue.enqueue("test_job", {"item": "beta"}, queue_name="test_worker_queue")

    # Dequeue and process using worker's internal mechanism
    msg1 = await queue.dequeue("test_worker_queue", timeout=0.1)
    assert msg1 is not None
    assert msg1.task_id == task_id1
    await worker._process_task(msg1)

    msg2 = await queue.dequeue("test_worker_queue", timeout=0.1)
    assert msg2 is not None
    assert msg2.task_id == task_id2
    await worker._process_task(msg2)

    assert processed_tasks == ["alpha", "beta"]
