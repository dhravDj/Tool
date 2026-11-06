"""Batch Orchestration and Lifecycle Manager for Large-Scale Ingestion (Phase 12).

Manages high-volume file batches, idempotent job creation, priority queue dispatch,
and accurate work-based progress calculation.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    BatchFileRecord,
    ProcessingBatchRecord,
    ProcessingJobRecord,
)
from app.modules.bulk_processing.queue.priority_queue import priority_task_queue
from app.modules.bulk_processing.schemas.batch import (
    BatchCreateRequest,
    BatchFileItem,
    BatchProgressResponse,
    BatchReportResponse,
    ProcessingBatchResponse,
)

logger = logging.getLogger(__name__)


class BatchManager:
    """Orchestrates batches of files, job creation, and batch lifecycle state machines."""

    async def create_batch(
        self,
        session: AsyncSession,
        request: BatchCreateRequest,
        owner_id: uuid.UUID | None = None,
    ) -> ProcessingBatchResponse:
        """Create a new batch container."""
        batch = ProcessingBatchRecord(
            name=request.name,
            owner_id=owner_id,
            status="pending",
            processing_policy=request.policy.model_dump(),
        )
        session.add(batch)
        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def get_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Retrieve a single batch by ID."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = select(ProcessingBatchRecord).where(ProcessingBatchRecord.id == b_uuid)
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")
        return self._to_batch_response(batch)

    async def add_files_to_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
        files_data: list[dict[str, Any]],
    ) -> ProcessingBatchResponse:
        """Registers a list of files into the batch with bounded batch inserts.

        files_data item:
            {
                "filename": str,
                "file_size": int,
                "sha256": str,
                "file_id": uuid.UUID | None,
                "status": "accepted" | "rejected",
                "validation_error": str | None,
                "dedup_decision": str,
            }
        """
        b_uuid = uuid.UUID(str(batch_id))
        stmt = select(ProcessingBatchRecord).where(ProcessingBatchRecord.id == b_uuid)
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        # Insert in chunks of 100 to avoid large memory/SQL locks
        chunk_size = 100
        total_size = batch.total_size_bytes

        for i in range(0, len(files_data), chunk_size):
            chunk = files_data[i : i + chunk_size]
            batch_files = []
            for item in chunk:
                bf = BatchFileRecord(
                    batch_id=batch.id,
                    file_id=item.get("file_id"),
                    filename=item["filename"],
                    file_size=item.get("file_size", 0),
                    sha256=item.get("sha256"),
                    status=item.get("status", "accepted"),
                    validation_error=item.get("validation_error"),
                    dedup_decision=item.get("dedup_decision", "new"),
                )
                batch_files.append(bf)
                total_size += item.get("file_size", 0)

            session.add_all(batch_files)
            await session.flush()

        # Update batch summary counts
        batch.total_files += len(files_data)
        batch.total_size_bytes = total_size
        batch.accepted_files += sum(1 for f in files_data if f.get("status") == "accepted")
        batch.rejected_files += sum(1 for f in files_data if f.get("status") == "rejected")
        batch.queued_files = batch.accepted_files
        batch.updated_at = datetime.now(UTC)

        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def start_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Starts batch processing by enqueuing jobs for all accepted files."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = (
            select(ProcessingBatchRecord)
            .where(ProcessingBatchRecord.id == b_uuid)
            .options(selectinload(ProcessingBatchRecord.files))
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        if batch.status in ("processing", "completed"):
            return self._to_batch_response(batch)

        batch.status = "processing"
        batch.started_at = datetime.now(UTC)
        policy = batch.processing_policy or {}
        prio = policy.get("priority", 30)

        # Create and enqueue jobs for accepted files
        chunk_size = 100
        accepted_files = [bf for bf in batch.files if bf.status in ("accepted", "queued") and bf.file_id is not None]

        for i in range(0, len(accepted_files), chunk_size):
            chunk = accepted_files[i : i + chunk_size]
            new_jobs = []
            for bf in chunk:
                # Idempotency key per batch + file
                idempotency_key = f"batch_{batch.id}_file_{bf.file_id}"
                job = ProcessingJobRecord(
                    batch_id=batch.id,
                    batch_file_id=bf.id,
                    file_id=bf.file_id,
                    priority=prio,
                    stage="queued",
                    status="queued",
                    idempotency_key=idempotency_key,
                )
                new_jobs.append(job)
                bf.status = "queued"

            session.add_all(new_jobs)
            await session.flush()

            # Enqueue to priority task queue
            for j in new_jobs:
                await priority_task_queue.enqueue(
                    task_name="execute_file_pipeline",
                    payload={"job_id": str(j.id), "file_id": str(j.file_id), "batch_id": str(batch.id)},
                    priority=prio,
                    user_id=str(batch.owner_id) if batch.owner_id else None,
                    idempotency_key=j.idempotency_key,
                    batch_id=str(batch.id),
                    job_id=str(j.id),
                )

        batch.queued_files = len(accepted_files)
        batch.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def pause_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Pauses processing on a batch."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = select(ProcessingBatchRecord).where(ProcessingBatchRecord.id == b_uuid)
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        batch.status = "paused"
        batch.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def resume_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Resumes a paused batch."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = select(ProcessingBatchRecord).where(ProcessingBatchRecord.id == b_uuid)
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        batch.status = "processing"
        batch.updated_at = datetime.now(UTC)
        await session.commit()
        return await self.start_batch(session, batch_id)

    async def cancel_batch(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Cancels a batch and cancels all queued or retrying jobs."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = (
            select(ProcessingBatchRecord)
            .where(ProcessingBatchRecord.id == b_uuid)
            .options(selectinload(ProcessingBatchRecord.jobs))
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        batch.status = "cancelled"
        batch.completed_at = datetime.now(UTC)
        batch.updated_at = datetime.now(UTC)

        for job in batch.jobs:
            if job.status in ("queued", "retrying", "pending"):
                job.status = "cancelled"
                await priority_task_queue.cancel_task(str(job.id))

        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def retry_failed_files(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> ProcessingBatchResponse:
        """Re-queues only failed files and jobs within a batch."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = (
            select(ProcessingBatchRecord)
            .where(ProcessingBatchRecord.id == b_uuid)
            .options(selectinload(ProcessingBatchRecord.jobs))
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        policy = batch.processing_policy or {}
        prio = policy.get("priority", 30)

        retried_count = 0
        for job in batch.jobs:
            if job.status in ("failed", "dead_letter"):
                job.status = "queued"
                job.retry_count = 0
                job.error_message = None
                job.error_code = None
                retried_count += 1
                await priority_task_queue.enqueue(
                    task_name="execute_file_pipeline",
                    payload={"job_id": str(job.id), "file_id": str(job.file_id), "batch_id": str(batch.id)},
                    priority=prio,
                    user_id=str(batch.owner_id) if batch.owner_id else None,
                    idempotency_key=f"{job.idempotency_key}_retry_{datetime.now(UTC).timestamp()}",
                    batch_id=str(batch.id),
                    job_id=str(job.id),
                )

        batch.status = "processing"
        batch.failed_files = max(0, batch.failed_files - retried_count)
        batch.queued_files += retried_count
        batch.updated_at = datetime.now(UTC)

        await session.commit()
        await session.refresh(batch)
        return self._to_batch_response(batch)

    async def get_batch_progress(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> BatchProgressResponse:
        """Computes true work-based progress, counts, and estimated completion time."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = (
            select(ProcessingBatchRecord)
            .where(ProcessingBatchRecord.id == b_uuid)
            .options(selectinload(ProcessingBatchRecord.jobs))
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        total_jobs = len(batch.jobs)
        if total_jobs > 0:
            completed_count = sum(1 for j in batch.jobs if j.status == "completed")
            failed_count = sum(1 for j in batch.jobs if j.status in ("failed", "dead_letter"))
            processing_count = sum(1 for j in batch.jobs if j.status == "processing")
            queued_count = sum(1 for j in batch.jobs if j.status in ("queued", "retrying"))

            # Calculate true weighted progress based on individual stage progress
            total_progress_sum = sum(j.progress for j in batch.jobs)
            overall_progress = round(total_progress_sum / total_jobs, 1)

            # Update batch entity
            batch.completed_files = completed_count
            batch.failed_files = failed_count
            batch.processing_files = processing_count
            batch.queued_files = queued_count
            batch.overall_progress = overall_progress

            if completed_count + failed_count >= total_jobs and total_jobs > 0:
                batch.status = "completed" if failed_count == 0 else "partially_completed"
                if not batch.completed_at:
                    batch.completed_at = datetime.now(UTC)
                await session.commit()
        else:
            completed_count = batch.completed_files
            failed_count = batch.failed_files
            processing_count = batch.processing_files
            queued_count = batch.queued_files
            overall_progress = batch.overall_progress

        elapsed_seconds = None
        rem_seconds = None
        throughput = None
        if batch.started_at:
            started = batch.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)
            elapsed_seconds = (datetime.now(UTC) - started).total_seconds()
            if elapsed_seconds > 0 and completed_count > 0:
                throughput = round(completed_count / elapsed_seconds, 2)
                remaining_files = max(0, batch.total_files - completed_count - failed_count)
                rem_seconds = round(remaining_files / throughput, 1) if throughput > 0 else None

        return BatchProgressResponse(
            batch_id=str(batch.id),
            status=batch.status,
            overall_progress=overall_progress,
            total_files=batch.total_files,
            completed_files=completed_count,
            failed_files=failed_count,
            processing_files=processing_count,
            queued_files=queued_count,
            elapsed_seconds=round(elapsed_seconds, 1) if elapsed_seconds is not None else None,
            estimated_remaining_seconds=rem_seconds,
            current_throughput_files_per_sec=throughput,
        )

    async def export_batch_report(
        self,
        session: AsyncSession,
        batch_id: uuid.UUID | str,
    ) -> BatchReportResponse:
        """Generates comprehensive audit report for a batch."""
        b_uuid = uuid.UUID(str(batch_id))
        stmt = (
            select(ProcessingBatchRecord)
            .where(ProcessingBatchRecord.id == b_uuid)
            .options(
                selectinload(ProcessingBatchRecord.files),
                selectinload(ProcessingBatchRecord.jobs),
            )
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found.")

        file_items = [
            BatchFileItem(
                id=str(bf.id),
                file_id=str(bf.file_id) if bf.file_id else None,
                filename=bf.filename,
                file_size=bf.file_size,
                sha256=bf.sha256,
                status=bf.status,
                validation_error=bf.validation_error,
                dedup_decision=bf.dedup_decision,
                created_at=bf.created_at.isoformat(),
            )
            for bf in batch.files
        ]

        errors = []
        for j in batch.jobs:
            if j.error_message:
                errors.append(
                    {
                        "job_id": str(j.id),
                        "file_id": str(j.file_id),
                        "error_code": j.error_code,
                        "error_message": j.error_message,
                        "retry_count": j.retry_count,
                    }
                )

        return BatchReportResponse(
            batch_id=str(batch.id),
            name=batch.name,
            status=batch.status,
            summary_metrics={
                "total_files": batch.total_files,
                "accepted_files": batch.accepted_files,
                "rejected_files": batch.rejected_files,
                "completed_files": batch.completed_files,
                "failed_files": batch.failed_files,
                "total_size_bytes": batch.total_size_bytes,
                "overall_progress": batch.overall_progress,
            },
            policy=batch.processing_policy or {},
            files=file_items,
            errors=errors,
            execution_timeline={
                "created_at": batch.created_at.isoformat(),
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            },
            exported_at=datetime.now(UTC).isoformat(),
        )

    def _to_batch_response(self, batch: ProcessingBatchRecord) -> ProcessingBatchResponse:
        return ProcessingBatchResponse(
            id=str(batch.id),
            name=batch.name,
            status=batch.status,
            total_files=batch.total_files,
            accepted_files=batch.accepted_files,
            rejected_files=batch.rejected_files,
            queued_files=batch.queued_files,
            processing_files=batch.processing_files,
            completed_files=batch.completed_files,
            partially_completed_files=batch.partially_completed_files,
            failed_files=batch.failed_files,
            cancelled_files=batch.cancelled_files,
            total_size_bytes=batch.total_size_bytes,
            overall_progress=batch.overall_progress,
            processing_policy=batch.processing_policy or {},
            error_summary=batch.error_summary or {},
            started_at=batch.started_at.isoformat() if batch.started_at else None,
            completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
            created_at=batch.created_at.isoformat(),
            updated_at=batch.updated_at.isoformat(),
        )


batch_manager = BatchManager()
