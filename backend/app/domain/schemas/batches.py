"""Batch processing schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import BatchStatus


class BatchCreateSchema(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Human-readable batch identifier"
    )


class BatchSummarySchema(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID | None = None
    name: str
    total_files: int
    queued_files: int
    processing_files: int
    completed_files: int
    failed_files: int
    cancelled_files: int
    status: BatchStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
