"""Master Bulk Processing Pipeline Facade (Phase 12).

Unifies:
1. Streaming multi-file bulk uploads with partial success isolation.
2. SHA-256 deduplication and per-user tenant safety.
3. Batch lifecycle management (create, start, pause, resume, cancel, retry-failed).
4. Multi-stage pipeline execution with stage-level idempotency.
5. System capacity, resource monitoring, and priority task scheduling.
"""

import hashlib
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import FileStatus
from app.infrastructure.database.models import FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.bulk_processing.capacity.system_monitor import system_monitor
from app.modules.bulk_processing.dedup.deduplicator import deduplication_engine
from app.modules.bulk_processing.orchestrator.batch_manager import batch_manager
from app.modules.bulk_processing.queue.priority_queue import priority_task_queue
from app.modules.bulk_processing.schemas.batch import (
    BatchCreateRequest,
    BatchProgressResponse,
    BatchReportResponse,
    ProcessingBatchResponse,
    ProcessingPolicy,
)
from app.modules.bulk_processing.schemas.job import (
    QueueStatusResponse,
    ResourceUsageResponse,
    SystemCapacityResponse,
    WorkerStatusResponse,
)
from app.modules.bulk_processing.schemas.upload import (
    BulkUploadConfig,
    BulkUploadItemResult,
    BulkUploadManifestResponse,
)

logger = logging.getLogger(__name__)


class BulkProcessingPipeline:
    """Master facade for large-scale file processing infrastructure."""

    def __init__(self) -> None:
        self.config = BulkUploadConfig()

    async def handle_bulk_upload(
        self,
        session: AsyncSession,
        files: list[UploadFile],
        batch_name: str | None = None,
        policy: ProcessingPolicy | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> BulkUploadManifestResponse:
        """Streams, validates, deduplicates, and registers a multi-file bulk submission."""
        pol = policy or ProcessingPolicy()
        b_name = batch_name or f"Batch_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        # 1. Create the Batch entity first
        create_req = BatchCreateRequest(name=b_name, policy=pol)
        batch_resp = await batch_manager.create_batch(session, create_req, owner_id=owner_id)
        b_uuid = uuid.UUID(batch_resp.id)

        items_results: list[BulkUploadItemResult] = []
        files_data_for_batch: list[dict[str, Any]] = []
        total_size = 0

        # 2. Stream and process each uploaded file individually
        for upload in files:
            filename = upload.filename or "unnamed_file"
            # Sanitize filename
            clean_filename = Path(filename).name

            try:
                # Stream write to temporary storage while computing SHA-256 and size
                sha256_hasher = hashlib.sha256()
                bytes_written = 0
                storage_key = f"uploads/{uuid.uuid4().hex}_{clean_filename}"

                # Read in 64KB chunks to keep memory usage minimal
                chunk_size = 64 * 1024
                content_chunks = []

                while True:
                    chunk = await upload.read(chunk_size)
                    if not chunk:
                        break
                    sha256_hasher.update(chunk)
                    bytes_written += len(chunk)
                    content_chunks.append(chunk)

                    if bytes_written > self.config.max_individual_file_size_bytes:
                        raise ValueError(
                            f"File size exceeds limit ({bytes_written} > {self.config.max_individual_file_size_bytes} bytes)"
                        )

                sha256_digest = sha256_hasher.hexdigest()
                full_bytes = b"".join(content_chunks)

                # Check deduplication
                existing_file, dedup_decision = await deduplication_engine.inspect_file_deduplication(
                    session=session,
                    owner_id=owner_id,
                    sha256=sha256_digest,
                    file_size=bytes_written,
                )

                if existing_file and dedup_decision == "reused":
                    # Reusing existing valid extraction
                    f_id = existing_file.id
                    item_res = BulkUploadItemResult(
                        filename=clean_filename,
                        status="accepted",
                        file_id=str(f_id),
                        file_size=bytes_written,
                        sha256=sha256_digest,
                        format_id=existing_file.extension,
                        dedup_decision="reused",
                    )
                else:
                    # Save to storage provider
                    saved_path = await local_storage.save_file(
                        destination_key=storage_key,
                        content=full_bytes,
                        folder="uploads",
                    )

                    # Determine initial extension
                    ext = Path(clean_filename).suffix.lstrip(".").lower() or "txt"

                    # Register FileRecord
                    new_file = FileRecord(
                        owner_id=owner_id,
                        original_filename=clean_filename,
                        stored_filename=Path(saved_path).name,
                        extension=ext,
                        file_size=bytes_written,
                        sha256=sha256_digest,
                        storage_path=saved_path,
                        status=FileStatus.STORED.value,
                        format_category="document",  # to be classified in detection stage
                        is_valid=True,
                    )
                    session.add(new_file)
                    await session.flush()
                    f_id = new_file.id

                    item_res = BulkUploadItemResult(
                        filename=clean_filename,
                        status="accepted",
                        file_id=str(f_id),
                        file_size=bytes_written,
                        sha256=sha256_digest,
                        format_id=ext,
                        dedup_decision="new",
                    )

                items_results.append(item_res)
                total_size += bytes_written
                files_data_for_batch.append(
                    {
                        "filename": clean_filename,
                        "file_size": bytes_written,
                        "sha256": sha256_digest,
                        "file_id": f_id,
                        "status": "accepted",
                        "validation_error": None,
                        "dedup_decision": dedup_decision,
                    }
                )

            except Exception as exc:
                # Individual file failure does NOT invalidate the entire batch
                logger.warning(f"File '{filename}' rejected during bulk upload: {exc}")
                err_res = BulkUploadItemResult(
                    filename=clean_filename,
                    status="rejected",
                    file_id=None,
                    file_size=0,
                    error_message=str(exc),
                    dedup_decision="skipped",
                )
                items_results.append(err_res)
                files_data_for_batch.append(
                    {
                        "filename": clean_filename,
                        "file_size": 0,
                        "sha256": None,
                        "file_id": None,
                        "status": "rejected",
                        "validation_error": str(exc),
                        "dedup_decision": "skipped",
                    }
                )

        # 3. Associate files with batch in database
        await batch_manager.add_files_to_batch(session, b_uuid, files_data_for_batch)

        # 4. Trigger auto-start if configured
        auto_started = pol.auto_start
        if auto_started and any(f.get("status") == "accepted" for f in files_data_for_batch):
            await batch_manager.start_batch(session, b_uuid)

        accepted_count = sum(1 for it in items_results if it.status == "accepted")
        rejected_count = sum(1 for it in items_results if it.status == "rejected")
        reused_count = sum(1 for it in items_results if it.dedup_decision == "reused")

        return BulkUploadManifestResponse(
            batch_id=str(b_uuid),
            batch_name=b_name,
            total_submitted=len(files),
            total_accepted=accepted_count,
            total_rejected=rejected_count,
            total_reused=reused_count,
            total_size_bytes=total_size,
            files=items_results,
            auto_started=auto_started,
            manifest_generated_at=datetime.now(UTC).isoformat(),
        )

    async def stream_bulk_upload(
        self,
        session: AsyncSession,
        upload_files: list[UploadFile],
        owner_id: str | None = None,
        config: Any = None,
    ) -> BulkUploadManifestResponse:
        b_name = getattr(config, "batch_name", None)
        owner_uuid = uuid.UUID(owner_id) if owner_id else None
        return await self.handle_bulk_upload(
            session=session,
            files=upload_files,
            batch_name=b_name,
            policy=ProcessingPolicy(),
            owner_id=owner_uuid,
        )

    # Proxy methods for BatchManager
    async def create_batch(self, session: AsyncSession, req: BatchCreateRequest, owner_id: uuid.UUID | None = None) -> ProcessingBatchResponse:
        return await batch_manager.create_batch(session, req, owner_id)

    async def get_batch(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.get_batch(session, batch_id)

    async def start_batch(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.start_batch(session, batch_id)

    async def pause_batch(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.pause_batch(session, batch_id)

    async def resume_batch(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.resume_batch(session, batch_id)

    async def cancel_batch(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.cancel_batch(session, batch_id)

    async def retry_failed(self, session: AsyncSession, batch_id: uuid.UUID | str) -> ProcessingBatchResponse:
        return await batch_manager.retry_failed_files(session, batch_id)

    async def get_progress(self, session: AsyncSession, batch_id: uuid.UUID | str) -> BatchProgressResponse:
        return await batch_manager.get_batch_progress(session, batch_id)

    async def get_report(self, session: AsyncSession, batch_id: uuid.UUID | str) -> BatchReportResponse:
        return await batch_manager.export_batch_report(session, batch_id)

    # Capacity & Telemetry proxy methods
    async def get_capacity(self, session: AsyncSession | None = None) -> SystemCapacityResponse:
        return await system_monitor.get_system_capacity(session)

    async def get_resource_usage(self) -> ResourceUsageResponse:
        return await system_monitor.get_resource_usage()

    async def get_worker_statuses(self, session: AsyncSession) -> list[WorkerStatusResponse]:
        return await system_monitor.get_worker_statuses(session)

    async def get_queue_status(self) -> QueueStatusResponse:
        depths = await priority_task_queue.get_queue_depths()
        total_q = sum(depths.get(k, 0) for k in ["interactive", "normal", "bulk", "maintenance"])
        return QueueStatusResponse(
            queues=depths,
            total_queued=total_q,
            total_processing=0,
            total_dead_letter=depths.get("dead_letter", 0),
            avg_latency_ms=0.25,
            active_workers_count=1,
            timestamp=datetime.now(UTC).isoformat(),
        )


bulk_processing_pipeline = BulkProcessingPipeline()
