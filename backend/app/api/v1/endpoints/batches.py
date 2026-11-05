"""Batch management endpoints (Phase 1 foundational API)."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.exceptions import EntityNotFoundError
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.batches import BatchSummarySchema
from app.infrastructure.database.models import Batch

router = APIRouter(prefix="/batches", tags=["Batches & Jobs"])


@router.get("", response_model=APIResponse[list[BatchSummarySchema]])
async def list_batches(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[BatchSummarySchema]]:
    """List batches with pagination (returns clean empty list in Phase 1)."""
    stmt = select(Batch).order_by(Batch.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    records = result.scalars().all()

    items = [BatchSummarySchema.model_validate(r) for r in records]
    return APIResponse.ok(
        data=items,
        message="Batches retrieved successfully.",
        meta={"total": len(items), "limit": limit, "offset": offset},
    )


@router.get("/{batch_id}", response_model=APIResponse[BatchSummarySchema])
async def get_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[BatchSummarySchema]:
    """Retrieve details for a specific batch by its UUID."""
    record = await session.get(Batch, batch_id)
    if not record:
        raise EntityNotFoundError(f"Batch with ID {batch_id} not found.")
    return APIResponse.ok(
        data=BatchSummarySchema.model_validate(record),
        message="Batch retrieved successfully.",
    )
