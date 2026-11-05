"""Document job schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import JobStatus


class JobSummarySchema(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    file_id: uuid.UUID
    status: JobStatus
    retry_count: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
