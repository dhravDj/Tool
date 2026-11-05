"""File management schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import FileStatus


class FileMetadataSchema(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID | None = None
    original_filename: str
    stored_filename: str
    extension: str
    detected_mime_type: str | None = None
    file_size: int
    sha256: str
    storage_path: str
    status: FileStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    file_id: uuid.UUID
    filename: str
    file_size: int
    sha256: str
    status: FileStatus
    message: str = "File uploaded successfully."
