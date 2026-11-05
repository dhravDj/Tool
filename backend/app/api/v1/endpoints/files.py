"""File management endpoints (Phase 1 foundational API)."""

import uuid

from fastapi import APIRouter, Depends, Query
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
