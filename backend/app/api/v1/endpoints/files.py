"""File management endpoints (Phase 1 foundational API)."""

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.exceptions import EntityNotFoundError
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.files import FileMetadataSchema
from app.infrastructure.database.models import FileRecord

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
    """Delete a file record and remove its local storage payload."""
    record = await session.get(FileRecord, file_id)
    if not record:
        raise EntityNotFoundError(f"File with ID {file_id} not found.")

    if record.storage_path:
        Path(record.storage_path).unlink(missing_ok=True)

    await session.delete(record)
    await session.commit()

    return APIResponse.ok(
        data={"id": str(file_id), "deleted": True},
        message=f"File {record.original_filename} deleted successfully.",
    )
