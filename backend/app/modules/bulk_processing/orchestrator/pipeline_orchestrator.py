"""Multi-Stage Pipeline Orchestrator for Phase 12 Bulk Processing.

Orchestrates sequential, decoupled stages for an individual file:
1. Registration & Content Integrity
2. Format Detection & Safety Validation
3. Domain-Specific Extraction (Routing to Phases 3-10)
4. AI Knowledge Indexing & Embeddings (Phase 11)
5. Search Availability & Batch Finalization
"""

import logging
import time
import tracemalloc
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.hardware import hardware_governor
from app.infrastructure.database.models import (
    JobAttemptRecord,
    ProcessingJobRecord,
)
from app.infrastructure.storage.local import local_storage
from app.modules.ai_intelligence.pipeline import ai_intelligence_pipeline
from app.modules.archive_intelligence.pipeline import archive_pipeline
from app.modules.audio_intelligence.pipeline import audio_pipeline
from app.modules.code_intelligence.pipeline import code_pipeline
from app.modules.extraction.pipeline import extraction_pipeline
from app.modules.files.detection.detector import universal_detector
from app.modules.image_intelligence.pipeline import image_intelligence_pipeline
from app.modules.presentation_intelligence.pipeline import presentation_pipeline
from app.modules.spreadsheet_intelligence.pipeline import spreadsheet_pipeline
from app.modules.structured_data_intelligence.pipeline import structured_pipeline
from app.modules.video_intelligence.pipeline import video_pipeline

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Executes multi-stage file processing with stage-level recovery and non-duplicative execution."""

    async def execute_file_job(
        self,
        session: AsyncSession,
        job_id: uuid.UUID | str,
        worker_id: str = "worker-generic",
    ) -> dict[str, Any]:
        """Executes or resumes an individual file job across stages."""
        j_uuid = uuid.UUID(str(job_id))
        stmt = (
            select(ProcessingJobRecord)
            .where(ProcessingJobRecord.id == j_uuid)
            .options(
                selectinload(ProcessingJobRecord.file),
                selectinload(ProcessingJobRecord.batch_file),
                selectinload(ProcessingJobRecord.batch),
            )
        )
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ValueError(f"ProcessingJob {job_id} not found.")

        file_rec = job.file
        batch_rec = job.batch
        batch_file_rec = job.batch_file
        policy = batch_rec.processing_policy if batch_rec else {}

        # 1. Start execution attempt tracking
        tracemalloc.start()
        start_time = time.perf_counter()
        job.status = "processing"
        job.current_worker_id = worker_id
        job.started_at = datetime.now(UTC)
        job.heartbeat_at = datetime.now(UTC)

        attempt = JobAttemptRecord(
            job_id=job.id,
            attempt_number=job.retry_count + 1,
            worker_id=worker_id,
            started_at=datetime.now(UTC),
            status="running",
        )
        session.add(attempt)
        await session.commit()

        try:
            # -------------------------------------------------------------
            # Stage 1: Detection & Safety Validation
            # -------------------------------------------------------------
            if job.stage in ("queued", "registered"):
                logger.info(f"Job {job.id}: Running Detection & Safety for {file_rec.original_filename}")
                job.stage = "detection"
                job.progress = 20.0
                await session.commit()

                # Verify file storage existence
                resolved_path = local_storage.get_local_path(file_rec.storage_path)
                if not resolved_path or not resolved_path.exists():
                    raise FileNotFoundError(f"Storage path {file_rec.storage_path} is missing on disk.")

                # Execute detection if format not already verified
                if not file_rec.format_category or file_rec.status == "stored":
                    detection_result = await universal_detector.detect(resolved_path, file_rec.original_filename)
                    file_rec.detected_mime_type = detection_result.detected_mime_type
                    file_rec.extension = detection_result.actual_extension
                    file_rec.format_category = detection_result.format_category
                    file_rec.confidence_score = detection_result.confidence_score
                    file_rec.is_valid = detection_result.is_valid
                    file_rec.is_corrupted = detection_result.is_corrupted
                    file_rec.is_mismatch = detection_result.is_mismatch
                    file_rec.is_suspicious = detection_result.is_suspicious
                    if detection_result.is_corrupted or detection_result.is_suspicious:
                        raise ValueError(f"File failed safety checks: corrupted={detection_result.is_corrupted}, suspicious={detection_result.is_suspicious}")

                job.stage_progress["detection"] = "completed"
                job.stage = "safety_validated"
                job.progress = 40.0
                await session.commit()

            # -------------------------------------------------------------
            # Stage 2: Modality-Specific Extraction (Phases 3–10)
            # -------------------------------------------------------------
            if job.stage in ("safety_validated", "detection"):
                logger.info(f"Job {job.id}: Running Extraction for {file_rec.original_filename} ({file_rec.format_category})")
                job.stage = "extraction"
                job.progress = 50.0
                await session.commit()

                cat = (file_rec.format_category or "document").lower()
                ext = (file_rec.extension or "txt").lower()

                # Route under hardware governor slot
                async with hardware_governor.cpu_bound_slot():
                    if cat == "archive" or ext in ("zip", "tar", "gz", "7z", "bz2", "xz"):
                        await archive_pipeline.analyze_archive(
                            session=session,
                            file_record=file_rec,
                            mode="mode_b_extract_only",
                        )
                    elif cat == "spreadsheet" or ext in ("xlsx", "xls", "csv", "tsv", "ods"):
                        await spreadsheet_pipeline.analyze_file_record(
                            file_id=file_rec.id,
                            session=session,
                        )
                    elif cat == "presentation" or ext in ("pptx", "ppt", "odp"):
                        await presentation_pipeline.analyze_file_record(
                            file_id=file_rec.id,
                            session=session,
                        )
                    elif cat == "audio" or ext in ("mp3", "wav", "m4a", "aac", "flac", "ogg"):
                        await audio_pipeline.analyze_audio(
                            file_record=file_rec,
                            session=session,
                        )
                    elif cat == "video" or ext in ("mp4", "mkv", "mov", "avi", "webm"):
                        await video_pipeline.analyze_video(
                            file_record=file_rec,
                            session=session,
                        )
                    elif cat == "code" or ext in ("py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"):
                        await code_pipeline.analyze_code(
                            session=session,
                            file_record=file_rec,
                        )
                    elif cat == "structured_data" or ext in ("json", "xml", "yaml", "yml", "toml", "parquet"):
                        await structured_pipeline.analyze_structured_data(
                            session=session,
                            file_record=file_rec,
                        )
                    elif cat == "image" or ext in ("png", "jpeg", "jpg", "webp", "tiff", "bmp"):
                        await image_intelligence_pipeline.analyze_file_record(
                            file_id=file_rec.id,
                            session=session,
                        )
                    else:
                        # Standard Document Extraction (PDF, DOCX, TXT, MD, RTF, ODT, EPUB)
                        await extraction_pipeline.extract_document(
                            file_id=file_rec.id,
                            session=session,
                        )

                job.stage_progress["extraction"] = "completed"
                job.stage = "extracted"
                job.progress = 75.0
                await session.commit()

            # -------------------------------------------------------------
            # Stage 3: AI Knowledge Indexing & Embeddings (Phase 11)
            # -------------------------------------------------------------
            ai_indexing_enabled = policy.get("ai_indexing_enabled", True)
            if ai_indexing_enabled and job.stage in ("extracted", "extraction"):
                logger.info(f"Job {job.id}: Running AI Indexing for {file_rec.original_filename}")
                job.stage = "ai_indexing"
                job.progress = 85.0
                await session.commit()

                await ai_intelligence_pipeline.index_file(
                    session=session,
                    file_id=file_rec.id,
                    force_reindex=False,
                )

                job.stage_progress["ai_indexing"] = "completed"
                job.stage = "indexed"
                job.progress = 95.0
                await session.commit()

            # -------------------------------------------------------------
            # Stage 4: Job Completion & Metric Recording
            # -------------------------------------------------------------
            job.stage = "completed"
            job.status = "completed"
            job.progress = 100.0
            job.completed_at = datetime.now(UTC)

            if batch_file_rec:
                batch_file_rec.status = "completed"

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            attempt.status = "success"
            attempt.finished_at = datetime.now(UTC)
            attempt.duration_ms = elapsed_ms
            attempt.memory_peak_mb = peak_mem / (1024 * 1024)

            await session.commit()
            logger.info(f"Job {job.id} ({file_rec.original_filename}) completed successfully in {elapsed_ms:.1f}ms")
            return {
                "job_id": str(job.id),
                "status": "completed",
                "file_id": str(file_rec.id),
                "duration_ms": elapsed_ms,
            }

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            err_msg = str(exc)
            logger.error(f"Job {job.id} execution failed: {err_msg}", exc_info=True)

            job.retry_count += 1
            job.error_code = type(exc).__name__
            job.error_message = err_msg

            attempt.status = "failed"
            attempt.finished_at = datetime.now(UTC)
            attempt.error_message = err_msg
            attempt.duration_ms = elapsed_ms
            attempt.memory_peak_mb = peak_mem / (1024 * 1024)

            if job.retry_count >= job.max_retries:
                job.status = "failed"
                if batch_file_rec:
                    batch_file_rec.status = "failed"
                    batch_file_rec.validation_error = err_msg
            else:
                job.status = "retrying"

            await session.commit()
            raise


pipeline_orchestrator = PipelineOrchestrator()
