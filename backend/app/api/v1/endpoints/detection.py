"""Universal file detection API endpoints."""

import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.config import settings
from app.core.exceptions import EntityNotFoundError, FileValidationError
from app.core.security import sanitize_filename
from app.domain.enums import FileStatus
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.detection import (
    AlternativeCandidateSchema,
    BatchDetectionResponse,
    DetectionEvidenceSchema,
    DetectionResultSchema,
)
from app.infrastructure.database.models import FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.files.detection.detector import universal_detector
from app.modules.formats.categories import FormatCategory
from app.modules.formats.registry import format_registry

router = APIRouter(prefix="/files", tags=["Universal File Detection"])


def _convert_result_to_schema(res: Any, persisted_id: str | None = None) -> DetectionResultSchema:
    """Helper to convert detection dataclass to Pydantic schema."""
    return DetectionResultSchema(
        format_id=res.format_id,
        canonical_name=res.canonical_name,
        display_name=res.display_name,
        mime_type=res.mime_type,
        extension=res.extension,
        claimed_extension=res.claimed_extension,
        category=res.category.value
        if isinstance(res.category, FormatCategory)
        else str(res.category),
        confidence_level=res.confidence_level.value,
        confidence_score=round(res.confidence_score, 4),
        support_status=res.support_status.value,
        is_valid=res.is_valid,
        is_mismatch=res.is_mismatch,
        is_corrupted=res.is_corrupted,
        is_suspicious=res.is_suspicious,
        is_container=res.is_container,
        container_type=res.container_type,
        evidence=[
            DetectionEvidenceSchema(
                signal=e.signal.value,
                format_id=e.format_id,
                mime_type=e.mime_type,
                confidence_score=e.confidence_score,
                details=e.details,
            )
            for e in res.evidence
        ],
        warnings=res.warnings,
        alternative_candidates=[
            AlternativeCandidateSchema(
                format_id=a.format_id,
                canonical_name=a.canonical_name,
                confidence_score=a.confidence_score,
                reason=a.reason,
            )
            for a in res.alternative_candidates
        ],
        metadata=res.metadata,
        file_size=res.file_size,
        sha256=res.sha256,
        detection_duration_ms=round(res.detection_duration_ms, 2),
        persisted_file_id=persisted_id,
    )


@router.post("/detect", response_model=APIResponse[DetectionResultSchema])
async def detect_single_file(
    file: UploadFile = File(..., description="Binary file to inspect and detect"),
    persist: bool = Query(
        True, description="Persist file to storage and record detection in database"
    ),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[DetectionResultSchema]:
    """Upload a single file, run universal 7-step detection, and optionally persist metadata."""
    safe_filename = sanitize_filename(file.filename or "uploaded_file")
    temp_dir = Path(tempfile.mkdtemp(prefix="documind_detect_"))
    temp_file_path = temp_dir / safe_filename

    try:
        # Stream file to secure temporary disk buffer with size check
        size = 0
        with open(temp_file_path, "wb") as f:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_BYTES:
                    raise FileValidationError(
                        f"File size exceeds maximum permitted limit ({settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB)."
                    )
                f.write(chunk)

        # Execute 7-step detection pipeline
        detection_res = universal_detector.detect_file(
            file_path=temp_file_path,
            original_filename=file.filename,
        )

        persisted_id: str | None = None
        if persist and detection_res.is_valid:
            # Generate storage keys
            file_uuid = uuid.uuid4()
            storage_key = f"{file_uuid}_{safe_filename}"
            # Save to permanent storage
            with open(temp_file_path, "rb") as f:
                relative_path = await local_storage.save_file(storage_key, f, folder="uploads")

            # Create database record
            db_record = FileRecord(
                id=file_uuid,
                original_filename=file.filename or "unknown",
                stored_filename=storage_key,
                extension=detection_res.extension
                or Path(safe_filename).suffix.lstrip(".")
                or "bin",
                detected_mime_type=detection_res.mime_type,
                file_size=detection_res.file_size,
                sha256=detection_res.sha256,
                storage_path=relative_path,
                status=FileStatus.STORED.value,
                # Phase 2 metadata
                detection_format_id=detection_res.format_id,
                claimed_extension=detection_res.claimed_extension,
                actual_extension=detection_res.extension,
                format_category=detection_res.category.value,
                confidence_level=detection_res.confidence_level.value,
                confidence_score=detection_res.confidence_score,
                support_status=detection_res.support_status.value,
                is_valid=detection_res.is_valid,
                is_mismatch=detection_res.is_mismatch,
                is_corrupted=detection_res.is_corrupted,
                is_suspicious=detection_res.is_suspicious,
                detection_evidence={"items": [e.details for e in detection_res.evidence]},
                detection_warnings=detection_res.warnings,
                file_metadata=detection_res.metadata,
                detection_engine_version="2.0.0",
                detected_at=datetime.now(UTC),
            )
            session.add(db_record)
            await session.commit()
            persisted_id = str(file_uuid)

        schema_res = _convert_result_to_schema(detection_res, persisted_id=persisted_id)
        return APIResponse.ok(
            data=schema_res,
            message=f"Detection complete: {schema_res.canonical_name} ({schema_res.confidence_level.upper()} confidence).",
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/detect/batch", response_model=APIResponse[BatchDetectionResponse])
async def detect_batch_files(
    files: list[UploadFile] = File(..., description="Batch of files to detect"),
    persist: bool = Query(False, description="Persist detected files to storage"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[BatchDetectionResponse]:
    """Execute concurrent detection on a controlled batch of files."""
    import asyncio

    if len(files) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch upload limited to 50 files per request.",
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="documind_batch_"))
    try:
        # 1. Save uploaded files to temp directory
        file_tasks_input: list[tuple[Path, str | None]] = []
        for file in files:
            safe_filename = sanitize_filename(file.filename or "batch_file")
            temp_file_path = temp_dir / f"{uuid.uuid4()}_{safe_filename}"
            size = 0
            with open(temp_file_path, "wb") as f:
                while chunk := await file.read(65536):
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_SIZE_BYTES:
                        break
                    f.write(chunk)
            file_tasks_input.append((temp_file_path, file.filename))

        # 2. Concurrently detect files with bounded worker pool (Semaphore 8)
        semaphore = asyncio.Semaphore(8)

        async def _detect_single(path: Path, orig_name: str | None) -> Any:
            async with semaphore:
                return await asyncio.to_thread(
                    universal_detector.detect_file,
                    file_path=path,
                    original_filename=orig_name,
                )

        detection_results = await asyncio.gather(
            *(_detect_single(p, n) for p, n in file_tasks_input)
        )

        results: list[DetectionResultSchema] = []
        mismatch_count = 0
        suspicious_count = 0

        for det_res in detection_results:
            if det_res.is_mismatch:
                mismatch_count += 1
            if det_res.is_suspicious or det_res.is_corrupted:
                suspicious_count += 1
            results.append(_convert_result_to_schema(det_res))

        summary = BatchDetectionResponse(
            total_files=len(files),
            successful_detections=len([r for r in results if r.is_valid]),
            mismatched_extensions=mismatch_count,
            suspicious_files=suspicious_count,
            results=results,
        )
        return APIResponse.ok(
            data=summary, message=f"Batch detection complete for {len(files)} files."
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{file_id}/detection", response_model=APIResponse[DetectionResultSchema])
async def get_persisted_detection(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[DetectionResultSchema]:
    """Retrieve persisted detection analysis results for a previously stored file."""
    record = await session.get(FileRecord, file_id)
    if not record:
        raise EntityNotFoundError(f"File with ID {file_id} not found.")

    if not record.detection_format_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File has not undergone Phase 2 detection analysis.",
        )

    fmt = format_registry.get_by_id(record.detection_format_id)
    data = DetectionResultSchema(
        format_id=record.detection_format_id,
        canonical_name=fmt.canonical_name if fmt else record.detection_format_id,
        display_name=fmt.display_name if fmt else record.detection_format_id.upper(),
        mime_type=record.detected_mime_type or "application/octet-stream",
        extension=record.actual_extension or record.extension,
        claimed_extension=record.claimed_extension,
        category=record.format_category or "unknown",
        confidence_level=record.confidence_level or "unknown",
        confidence_score=record.confidence_score or 0.0,
        support_status=record.support_status or "unknown",
        is_valid=record.is_valid,
        is_mismatch=record.is_mismatch,
        is_corrupted=record.is_corrupted,
        is_suspicious=record.is_suspicious,
        is_container=fmt.is_container if fmt else False,
        container_type=fmt.container_type if fmt else None,
        evidence=[],
        warnings=record.detection_warnings if isinstance(record.detection_warnings, list) else [],
        alternative_candidates=[],
        metadata=record.file_metadata if isinstance(record.file_metadata, dict) else {},
        file_size=record.file_size,
        sha256=record.sha256,
        detection_duration_ms=0.0,
        persisted_file_id=str(record.id),
    )
    return APIResponse.ok(data=data, message="Persisted detection retrieved.")
