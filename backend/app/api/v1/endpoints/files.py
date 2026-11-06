"""File management endpoints (Phase 1 foundational API)."""

import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.exceptions import EntityNotFoundError
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.files import FileMetadataSchema
from app.infrastructure.database.models import (
    ArchiveAnalysisRecord,
    ArchiveEntryRecord,
    ArchiveRelationshipRecord,
    AudioAnalysisRecord,
    BatchFileRecord,
    CodeAnalysisRecord,
    EmbeddingRecord,
    ExtractionRecord,
    FileRecord,
    ImageAnalysisRecord,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    PresentationAnalysisRecord,
    ProcessingJobRecord,
    SpreadsheetAnalysisRecord,
    StructuredDataAnalysisRecord,
    SummaryRecord,
    VideoAnalysisRecord,
)

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("", response_model=APIResponse[list[FileMetadataSchema]])
async def list_files(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[FileMetadataSchema]]:
    """List uploaded file records with pagination (returns clean empty list in Phase 1)."""
    stmt = select(FileRecord).order_by(FileRecord.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    records = result.scalars().all()

    items = [FileMetadataSchema.model_validate(r) for r in records]
    return APIResponse.ok(
        data=items,
        message="Files retrieved successfully.",
        meta={"total": len(items), "limit": limit, "offset": offset},
    )


@router.get("/{file_id}", response_model=APIResponse[FileMetadataSchema])
async def get_file(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[FileMetadataSchema]:
    """Retrieve metadata for a specific file by its UUID."""
    record = await session.get(FileRecord, file_id)
    if not record:
        raise EntityNotFoundError(f"File with ID {file_id} not found.")
    return APIResponse.ok(
        data=FileMetadataSchema.model_validate(record),
        message="File metadata retrieved.",
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Download the original uploaded file payload."""
    record = await session.get(FileRecord, file_id)
    if not record:
        raise EntityNotFoundError(f"File with ID {file_id} not found.")

    p = Path(record.storage_path)
    if not p.is_file():
        raise EntityNotFoundError("Original physical file not found on storage disk.")

    media_type = record.detected_mime_type or "application/octet-stream"
    return FileResponse(
        path=str(p),
        filename=record.original_filename,
        media_type=media_type,
    )


@router.delete("/{file_id}", response_model=APIResponse[dict[str, Any]])
async def delete_file(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Delete a file record, its local storage payload, and all derived intelligence assets in dependency-safe order."""
    record = await session.get(FileRecord, file_id)
    if not record:
        raise EntityNotFoundError(f"File with ID {file_id} not found.")

    # 1. Clean up physical original file and derived directories
    if record.storage_path:
        Path(record.storage_path).unlink(missing_ok=True)

    storage_root = Path("./storage")
    extracted_dir = storage_root / "extracted" / str(file_id)
    if extracted_dir.is_dir():
        shutil.rmtree(extracted_dir, ignore_errors=True)

    keyframe_dir = storage_root / "keyframes" / str(file_id)
    if keyframe_dir.is_dir():
        shutil.rmtree(keyframe_dir, ignore_errors=True)

    # 2. Dependency-safe database cascading deletion
    chunk_ids_subquery = select(KnowledgeChunkRecord.id).where(KnowledgeChunkRecord.file_id == file_id)
    await session.execute(delete(EmbeddingRecord).where(EmbeddingRecord.chunk_id.in_(chunk_ids_subquery)))
    await session.execute(delete(KnowledgeChunkRecord).where(KnowledgeChunkRecord.file_id == file_id))
    await session.execute(delete(KnowledgeDocumentRecord).where(KnowledgeDocumentRecord.file_id == file_id))
    await session.execute(delete(SummaryRecord).where(SummaryRecord.file_id == file_id))

    await session.execute(
        delete(ArchiveRelationshipRecord).where(
            (ArchiveRelationshipRecord.parent_file_id == file_id)
            | (ArchiveRelationshipRecord.child_file_id == file_id)
        )
    )
    archive_ids_subquery = select(ArchiveAnalysisRecord.id).where(ArchiveAnalysisRecord.file_id == file_id)
    await session.execute(delete(ArchiveEntryRecord).where(ArchiveEntryRecord.archive_analysis_id.in_(archive_ids_subquery)))
    await session.execute(delete(ArchiveAnalysisRecord).where(ArchiveAnalysisRecord.file_id == file_id))
    await session.execute(delete(StructuredDataAnalysisRecord).where(StructuredDataAnalysisRecord.file_id == file_id))
    await session.execute(delete(CodeAnalysisRecord).where(CodeAnalysisRecord.file_id == file_id))
    await session.execute(delete(VideoAnalysisRecord).where(VideoAnalysisRecord.file_id == file_id))
    await session.execute(delete(AudioAnalysisRecord).where(AudioAnalysisRecord.file_id == file_id))
    await session.execute(delete(PresentationAnalysisRecord).where(PresentationAnalysisRecord.file_id == file_id))
    await session.execute(delete(SpreadsheetAnalysisRecord).where(SpreadsheetAnalysisRecord.file_id == file_id))
    await session.execute(delete(ImageAnalysisRecord).where(ImageAnalysisRecord.file_id == file_id))
    await session.execute(delete(ExtractionRecord).where(ExtractionRecord.file_id == file_id))
    await session.execute(delete(ProcessingJobRecord).where(ProcessingJobRecord.file_id == file_id))
    await session.execute(delete(BatchFileRecord).where(BatchFileRecord.file_id == file_id))

    # 3. Delete parent FileRecord
    await session.delete(record)
    await session.commit()

    return APIResponse.ok(
        data={"id": str(file_id), "deleted": True},
        message=f"File {record.original_filename} and all associated intelligence assets deleted successfully.",
    )
