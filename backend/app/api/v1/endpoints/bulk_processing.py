"""Bulk processing, batch management, and job scheduling endpoints (Phase 12)."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.database import get_session
from app.core.exceptions import EntityNotFoundError
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import (
    BatchFileRecord,
    JobAttemptRecord,
    ProcessingBatchRecord,
    ProcessingJobRecord,
)
from app.modules.bulk_processing.pipeline import bulk_processing_pipeline
from app.modules.bulk_processing.queue.priority_queue import priority_task_queue
from app.modules.bulk_processing.schemas.batch import (
    BatchCreateRequest,
    BatchFileItem,
    BatchProgressResponse,
    BatchReportResponse,
    ProcessingBatchResponse,
)
from app.modules.bulk_processing.schemas.job import (
    JobAttemptResponse,
    JobResponse,
    QueueStatusResponse,
)
from app.modules.bulk_processing.schemas.upload import (
    BulkUploadConfig,
    BulkUploadManifestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()
bulk_router = APIRouter(prefix="/bulk", tags=["Bulk Processing & Batches"])
jobs_router = APIRouter(prefix="/jobs", tags=["Processing Jobs & Tasks"])


def _to_job_response(job: ProcessingJobRecord, filename: str | None = None) -> JobResponse:
    fn = filename
    if not fn and hasattr(job, "batch_file") and job.batch_file:
        fn = job.batch_file.filename
    return JobResponse(
        id=str(job.id),
        batch_id=str(job.batch_id) if job.batch_id else None,
        batch_file_id=str(job.batch_file_id) if job.batch_file_id else None,
        file_id=str(job.file_id),
        filename=fn,
        job_type=job.job_type,
        stage=job.stage,
        priority=job.priority,
        status=job.status,
        current_worker_id=job.current_worker_id,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        progress=job.progress,
        stage_progress=job.stage_progress or {},
        idempotency_key=job.idempotency_key,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else "",
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


def _to_attempt_response(att: JobAttemptRecord) -> JobAttemptResponse:
    return JobAttemptResponse(
        id=str(att.id),
        attempt_number=att.attempt_number,
        worker_id=att.worker_id,
        status=att.status,
        started_at=att.started_at.isoformat() if att.started_at else "",
        finished_at=att.finished_at.isoformat() if att.finished_at else None,
        error_message=att.error_message,
        duration_ms=att.duration_ms,
        memory_peak_mb=att.memory_peak_mb,
    )


def _to_batch_response(batch: ProcessingBatchRecord) -> ProcessingBatchResponse:
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
        created_at=batch.created_at.isoformat() if batch.created_at else "",
        updated_at=batch.updated_at.isoformat() if batch.updated_at else "",
    )


# ---------------------------------------------------------
# Bulk Endpoints (/bulk)
# ---------------------------------------------------------


@bulk_router.post("/upload", response_model=APIResponse[BulkUploadManifestResponse])
async def upload_bulk_files(
    files: list[UploadFile] = File(...),
    owner_id: str | None = Form(None),
    batch_name: str | None = Form(None),
    auto_create_batch: bool = Form(True),
    auto_start_batch: bool = Form(False),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[BulkUploadManifestResponse]:
    """Streamingly uploads multiple files, performs dedup & validation, and optionally registers a batch."""
    cfg = BulkUploadConfig(
        batch_name=batch_name,
        auto_create_batch=auto_create_batch,
        auto_start_batch=auto_start_batch,
    )
    manifest = await bulk_processing_pipeline.stream_bulk_upload(
        session=session,
        upload_files=files,
        owner_id=owner_id,
        config=cfg,
    )
    return APIResponse.ok(
        data=manifest,
        message=f"Successfully processed upload of {manifest.total_submitted} files.",
    )


@bulk_router.post("/batches", response_model=APIResponse[ProcessingBatchResponse])
async def create_batch(
    request: BatchCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Create a new batch container for high-volume file processing."""
    batch_resp = await bulk_processing_pipeline.create_batch(session, request)
    return APIResponse.ok(data=batch_resp, message="Batch created successfully.")


@bulk_router.get("/batches", response_model=APIResponse[list[ProcessingBatchResponse]])
async def list_batches(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    owner_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[ProcessingBatchResponse]]:
    """List processing batches with optional status or owner filters."""
    stmt = select(ProcessingBatchRecord)
    if status:
        stmt = stmt.where(ProcessingBatchRecord.status == status)
    if owner_id:
        try:
            stmt = stmt.where(ProcessingBatchRecord.owner_id == uuid.UUID(owner_id))
        except ValueError:
            pass

    stmt = stmt.order_by(ProcessingBatchRecord.created_at.desc()).limit(limit).offset(offset)
    res = await session.execute(stmt)
    records = res.scalars().all()
    items = [_to_batch_response(b) for b in records]

    # Total count query
    count_stmt = select(func.count(ProcessingBatchRecord.id))
    if status:
        count_stmt = count_stmt.where(ProcessingBatchRecord.status == status)
    if owner_id:
        try:
            count_stmt = count_stmt.where(ProcessingBatchRecord.owner_id == uuid.UUID(owner_id))
        except ValueError:
            pass
    total_res = await session.execute(count_stmt)
    total_count = total_res.scalar() or 0

    return APIResponse.ok(
        data=items,
        message="Batches retrieved successfully.",
        meta={"total": total_count, "limit": limit, "offset": offset},
    )


@bulk_router.get("/batches/{batch_id}", response_model=APIResponse[ProcessingBatchResponse])
async def get_batch_details(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Retrieve details for a specific processing batch."""
    try:
        batch_resp = await bulk_processing_pipeline.get_batch(session, batch_id)
        return APIResponse.ok(data=batch_resp, message="Batch retrieved successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.get("/batches/{batch_id}/files", response_model=APIResponse[list[BatchFileItem]])
async def list_batch_files(
    batch_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[BatchFileItem]]:
    """List files belonging to a batch with optional status filter."""
    stmt = select(BatchFileRecord).where(BatchFileRecord.batch_id == batch_id)
    if status:
        stmt = stmt.where(BatchFileRecord.status == status)
    stmt = stmt.order_by(BatchFileRecord.created_at.asc()).limit(limit).offset(offset)

    res = await session.execute(stmt)
    records = res.scalars().all()

    items = [
        BatchFileItem(
            id=str(bf.id),
            file_id=str(bf.file_id) if bf.file_id else None,
            filename=bf.filename,
            file_size=bf.file_size,
            sha256=bf.sha256,
            status=bf.status,
            validation_error=bf.validation_error,
            dedup_decision=bf.dedup_decision,
            created_at=bf.created_at.isoformat() if bf.created_at else "",
        )
        for bf in records
    ]

    count_stmt = select(func.count(BatchFileRecord.id)).where(BatchFileRecord.batch_id == batch_id)
    if status:
        count_stmt = count_stmt.where(BatchFileRecord.status == status)
    total_res = await session.execute(count_stmt)
    total_count = total_res.scalar() or 0

    return APIResponse.ok(
        data=items,
        message="Batch files retrieved successfully.",
        meta={"total": total_count, "limit": limit, "offset": offset},
    )


@bulk_router.post("/batches/{batch_id}/start", response_model=APIResponse[ProcessingBatchResponse])
async def start_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Start batch processing by enqueuing jobs for all accepted files."""
    try:
        resp = await bulk_processing_pipeline.start_batch(session, batch_id)
        return APIResponse.ok(data=resp, message="Batch execution started successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.post("/batches/{batch_id}/pause", response_model=APIResponse[ProcessingBatchResponse])
async def pause_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Pause execution of a running batch."""
    try:
        resp = await bulk_processing_pipeline.pause_batch(session, batch_id)
        return APIResponse.ok(data=resp, message="Batch paused successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.post("/batches/{batch_id}/resume", response_model=APIResponse[ProcessingBatchResponse])
async def resume_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Resume execution of a paused batch."""
    try:
        resp = await bulk_processing_pipeline.resume_batch(session, batch_id)
        return APIResponse.ok(data=resp, message="Batch resumed successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.post("/batches/{batch_id}/cancel", response_model=APIResponse[ProcessingBatchResponse])
async def cancel_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Cancel a batch and all associated queued jobs."""
    try:
        resp = await bulk_processing_pipeline.cancel_batch(session, batch_id)
        return APIResponse.ok(data=resp, message="Batch cancelled successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.post("/batches/{batch_id}/retry-failed", response_model=APIResponse[ProcessingBatchResponse])
async def retry_failed_files(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ProcessingBatchResponse]:
    """Re-enqueues only failed or dead-letter files within a batch."""
    try:
        resp = await bulk_processing_pipeline.retry_failed(session, batch_id)
        return APIResponse.ok(data=resp, message="Failed files re-queued for execution.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.get("/batches/{batch_id}/progress", response_model=APIResponse[BatchProgressResponse])
async def get_batch_progress(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[BatchProgressResponse]:
    """Get live work-weighted progress and completion estimation for a batch."""
    try:
        progress = await bulk_processing_pipeline.get_progress(session, batch_id)
        return APIResponse.ok(data=progress, message="Batch progress retrieved.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


@bulk_router.get("/batches/{batch_id}/report", response_model=APIResponse[BatchReportResponse])
async def get_batch_report(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[BatchReportResponse]:
    """Export complete audit report for a batch."""
    try:
        report = await bulk_processing_pipeline.get_report(session, batch_id)
        return APIResponse.ok(data=report, message="Batch report generated successfully.")
    except ValueError as err:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.") from err


# ---------------------------------------------------------
# Job Endpoints (/jobs)
# ---------------------------------------------------------


@jobs_router.get("/queue/status", response_model=APIResponse[QueueStatusResponse])
async def get_queue_status() -> APIResponse[QueueStatusResponse]:
    """Retrieve multi-tier queue depth, backlog metrics, and active worker count."""
    status = await bulk_processing_pipeline.get_queue_status()
    return APIResponse.ok(data=status, message="Queue status retrieved.")


@jobs_router.get("", response_model=APIResponse[list[JobResponse]])
async def list_jobs(
    batch_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    stage: str | None = Query(None),
    priority: int | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[JobResponse]]:
    """List pipeline jobs with filtering by batch, status, stage, and priority."""
    stmt = select(ProcessingJobRecord).options(selectinload(ProcessingJobRecord.batch_file))
    if batch_id:
        stmt = stmt.where(ProcessingJobRecord.batch_id == batch_id)
    if status:
        stmt = stmt.where(ProcessingJobRecord.status == status)
    if stage:
        stmt = stmt.where(ProcessingJobRecord.stage == stage)
    if priority is not None:
        stmt = stmt.where(ProcessingJobRecord.priority == priority)

    stmt = stmt.order_by(ProcessingJobRecord.created_at.desc()).limit(limit).offset(offset)
    res = await session.execute(stmt)
    records = res.scalars().all()
    items = [_to_job_response(j) for j in records]

    # Count
    count_stmt = select(func.count(ProcessingJobRecord.id))
    if batch_id:
        count_stmt = count_stmt.where(ProcessingJobRecord.batch_id == batch_id)
    if status:
        count_stmt = count_stmt.where(ProcessingJobRecord.status == status)
    if stage:
        count_stmt = count_stmt.where(ProcessingJobRecord.stage == stage)
    if priority is not None:
        count_stmt = count_stmt.where(ProcessingJobRecord.priority == priority)
    total_res = await session.execute(count_stmt)
    total_count = total_res.scalar() or 0

    return APIResponse.ok(
        data=items,
        message="Jobs retrieved successfully.",
        meta={"total": total_count, "limit": limit, "offset": offset},
    )


@jobs_router.get("/{job_id}", response_model=APIResponse[JobResponse])
async def get_job_details(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[JobResponse]:
    """Retrieve detailed state of a single processing job."""
    stmt = (
        select(ProcessingJobRecord)
        .where(ProcessingJobRecord.id == job_id)
        .options(selectinload(ProcessingJobRecord.batch_file))
    )
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise EntityNotFoundError(f"Job with ID {job_id} not found.")

    return APIResponse.ok(data=_to_job_response(job), message="Job details retrieved.")


@jobs_router.post("/{job_id}/cancel", response_model=APIResponse[JobResponse])
async def cancel_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[JobResponse]:
    """Cancel a pending or queued processing job."""
    stmt = (
        select(ProcessingJobRecord)
        .where(ProcessingJobRecord.id == job_id)
        .options(selectinload(ProcessingJobRecord.batch_file))
    )
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise EntityNotFoundError(f"Job with ID {job_id} not found.")

    if job.status not in ("completed", "cancelled"):
        job.status = "cancelled"
        await priority_task_queue.cancel_task(str(job.id))
        await session.commit()
        await session.refresh(job)

    return APIResponse.ok(data=_to_job_response(job), message="Job cancelled.")


@jobs_router.post("/{job_id}/retry", response_model=APIResponse[JobResponse])
async def retry_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[JobResponse]:
    """Retry a failed or dead-letter job."""
    stmt = (
        select(ProcessingJobRecord)
        .where(ProcessingJobRecord.id == job_id)
        .options(selectinload(ProcessingJobRecord.batch_file))
    )
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise EntityNotFoundError(f"Job with ID {job_id} not found.")

    job.status = "queued"
    job.error_message = None
    job.error_code = None
    job.retry_count = 0

    await priority_task_queue.enqueue(
        task_name="execute_file_pipeline",
        payload={
            "job_id": str(job.id),
            "file_id": str(job.file_id),
            "batch_id": str(job.batch_id) if job.batch_id else None,
        },
        priority=job.priority,
        idempotency_key=f"{job.idempotency_key}_retry_{datetime.now(UTC).timestamp()}",
        batch_id=str(job.batch_id) if job.batch_id else None,
        job_id=str(job.id),
    )

    await session.commit()
    await session.refresh(job)

    return APIResponse.ok(data=_to_job_response(job), message="Job re-queued successfully.")


@jobs_router.get("/{job_id}/attempts", response_model=APIResponse[list[JobAttemptResponse]])
async def get_job_attempts(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[JobAttemptResponse]]:
    """Retrieve full attempt history and execution telemetry for a job."""
    stmt = select(JobAttemptRecord).where(JobAttemptRecord.job_id == job_id).order_by(JobAttemptRecord.attempt_number.asc())
    res = await session.execute(stmt)
    records = res.scalars().all()
    items = [_to_attempt_response(a) for a in records]
    return APIResponse.ok(data=items, message="Job attempts retrieved.")


# Include sub-routers into main router
router.include_router(bulk_router)
router.include_router(jobs_router)
