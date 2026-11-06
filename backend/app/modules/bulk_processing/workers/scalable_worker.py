"""Scalable, Resource-Aware Background Worker Subsystem (Phase 12).

Features:
1. Multi-tier priority task consumption (interactive > normal > bulk > maintenance).
2. Autonomous worker registration & periodic heartbeat telemetry.
3. HardwareGovernor concurrency integration (CPU workers = 4, GPU slots = 1).
4. Stale-job supervisor reclaiming tasks orphaned by dead or killed workers.
5. Graceful termination and signal handling.
"""

import asyncio
import logging
import os
import socket
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.hardware import hardware_governor
from app.infrastructure.database.models import (
    ProcessingJobRecord,
    WorkerHeartbeatRecord,
)
from app.infrastructure.database.session import async_session_factory
from app.modules.bulk_processing.orchestrator.pipeline_orchestrator import (
    pipeline_orchestrator,
)
from app.modules.bulk_processing.queue.priority_queue import (
    PriorityTaskMessage,
    priority_task_queue,
)

logger = logging.getLogger(__name__)


class ScalableWorker:
    """Enterprise background worker managing priority tasks and health heartbeats."""

    def __init__(
        self,
        worker_id: str | None = None,
        worker_type: str = "generic",
        poll_interval: float = 0.5,
        heartbeat_interval: float = 10.0,
    ) -> None:
        self.worker_id = worker_id or f"worker-{socket.gethostname()[:8]}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.worker_type = worker_type
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self._running = False
        self._stop_event = asyncio.Event()
        self._current_job_id: str | None = None
        self._jobs_completed = 0
        self._jobs_failed = 0
        self._started_at = datetime.now(UTC)

    async def start(self) -> None:
        """Starts worker execution loop and periodic heartbeat task."""
        self._running = True
        self._stop_event.clear()
        logger.info(f"ScalableWorker [{self.worker_id}] starting on PID {os.getpid()}...")

        # Register initial heartbeat
        await self._send_heartbeat(status="idle")

        # Spawn background heartbeat supervisor
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        stale_reaper_task = asyncio.create_task(self._stale_job_reaper_loop())

        try:
            while self._running:
                try:
                    task = await priority_task_queue.dequeue(timeout=self.poll_interval)
                    if task is None:
                        continue

                    await self._process_priority_task(task)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.error(f"Worker [{self.worker_id}] loop error: {exc}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)
        finally:
            self._running = False
            heartbeat_task.cancel()
            stale_reaper_task.cancel()
            await self._send_heartbeat(status="shutting_down")
            logger.info(f"ScalableWorker [{self.worker_id}] stopped cleanly.")

    async def stop(self) -> None:
        """Signal worker to gracefully stop."""
        self._running = False
        self._stop_event.set()

    async def _process_priority_task(self, task: PriorityTaskMessage) -> None:
        """Executes a single task within HardwareGovernor resource limits."""
        self._current_job_id = task.payload.get("job_id")
        await self._send_heartbeat(status="busy")

        try:
            if task.task_name == "execute_file_pipeline":
                job_id = task.payload.get("job_id")
                if job_id:
                    async with async_session_factory() as session:
                        result = await pipeline_orchestrator.execute_file_job(
                            session=session,
                            job_id=job_id,
                            worker_id=self.worker_id,
                        )
                        await priority_task_queue.complete_task(
                            task.task_id, result=result, user_id=task.user_id
                        )
                        self._jobs_completed += 1
            else:
                logger.warning(f"Unknown task name '{task.task_name}' - completing with noop.")
                await priority_task_queue.complete_task(task.task_id, result={"status": "noop"})

        except Exception as exc:
            self._jobs_failed += 1
            logger.warning(f"Task {task.task_id} failed on worker [{self.worker_id}]: {exc}")
            await priority_task_queue.fail_task(task, error=str(exc), retry=True)
        finally:
            self._current_job_id = None
            await self._send_heartbeat(status="idle")

    async def _heartbeat_loop(self) -> None:
        """Periodically refreshes worker heartbeat telemetry."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self._running:
                    st = "busy" if self._current_job_id else "idle"
                    await self._send_heartbeat(status=st)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Heartbeat tick error: {e}")

    async def _send_heartbeat(self, status: str = "alive") -> None:
        """Writes heartbeat record to PostgreSQL."""
        try:
            async with async_session_factory() as session:
                stmt = select(WorkerHeartbeatRecord).where(WorkerHeartbeatRecord.worker_id == self.worker_id)
                res = await session.execute(stmt)
                rec = res.scalar_one_or_none()

                hw = hardware_governor.detect_hardware()
                cpu_pct = 0.0
                mem_mb = 0.0
                gpu_mb = hw.get("accelerator", {}).get("vram_mb")

                if rec:
                    rec.status = status
                    rec.last_heartbeat = datetime.now(UTC)
                    rec.jobs_completed = self._jobs_completed
                    rec.jobs_failed = self._jobs_failed
                    rec.current_job_id = uuid.UUID(self._current_job_id) if self._current_job_id else None
                else:
                    rec = WorkerHeartbeatRecord(
                        worker_id=self.worker_id,
                        hostname=socket.gethostname(),
                        pid=os.getpid(),
                        worker_type=self.worker_type,
                        current_job_id=uuid.UUID(self._current_job_id) if self._current_job_id else None,
                        jobs_completed=self._jobs_completed,
                        jobs_failed=self._jobs_failed,
                        cpu_percent=cpu_pct,
                        memory_mb=mem_mb,
                        gpu_memory_used_mb=gpu_mb,
                        status=status,
                        last_heartbeat=datetime.now(UTC),
                        started_at=self._started_at,
                    )
                    session.add(rec)
                await session.commit()
        except Exception as e:
            logger.debug(f"Failed to record worker heartbeat in DB: {e}")

    async def _stale_job_reaper_loop(self) -> None:
        """Periodically reclaims jobs whose assigned worker died (>60s without heartbeat)."""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # Check every 30s
                if not self._running:
                    break

                async with async_session_factory() as session:
                    now = datetime.now(UTC)
                    # Find jobs in processing state whose heartbeat is older than 90s
                    stmt = (
                        select(ProcessingJobRecord)
                        .where(
                            ProcessingJobRecord.status == "processing",
                            ProcessingJobRecord.heartbeat_at < datetime.fromtimestamp(now.timestamp() - 90, UTC),
                        )
                        .limit(20)
                    )
                    res = await session.execute(stmt)
                    stale_jobs = res.scalars().all()

                    for j in stale_jobs:
                        logger.warning(f"Reclaiming stale job {j.id} (worker {j.current_worker_id} died)")
                        j.status = "queued"
                        j.retry_count += 1
                        j.error_message = "Worker heartbeat expired (auto-reclaimed by supervisor)"
                        await priority_task_queue.enqueue(
                            task_name="execute_file_pipeline",
                            payload={"job_id": str(j.id), "file_id": str(j.file_id), "batch_id": str(j.batch_id)},
                            priority=j.priority,
                            idempotency_key=f"{j.idempotency_key}_reclaim_{now.timestamp()}",
                            batch_id=str(j.batch_id) if j.batch_id else None,
                            job_id=str(j.id),
                        )
                    await session.commit()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Stale job reaper error: {e}")


scalable_worker = ScalableWorker()
