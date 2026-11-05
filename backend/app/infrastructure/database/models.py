"""SQLAlchemy 2.0 declarative database models."""

import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.domain.enums import BatchStatus, FileStatus, JobStatus
from app.infrastructure.database.base import Base, TimestampMixin

# Use JSONB on PostgreSQL and JSON on SQLite for cross-platform support
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class User(Base, TimestampMixin):
    """Platform user entity."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    files: Mapped[list["FileRecord"]] = relationship("FileRecord", back_populates="owner")
    batches: Mapped[list["Batch"]] = relationship("Batch", back_populates="owner")


class FileRecord(Base):
    """Metadata record for every uploaded or ingested file."""

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    extension: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    detected_mime_type: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=FileStatus.PENDING.value, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="files")
    jobs: Mapped[list["DocumentJob"]] = relationship(
        "DocumentJob", back_populates="file", cascade="all, delete-orphan"
    )
    extractions: Mapped[list["ExtractionRecord"]] = relationship(
        "ExtractionRecord", back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_files_owner_status", "owner_id", "status"),
        Index("ix_files_sha256_size", "sha256", "file_size"),
    )


class Batch(Base, TimestampMixin):
    """Parent batch tracking high-volume file ingestion and processing operations."""

    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queued_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=BatchStatus.PENDING.value,
        index=True,
        nullable=False,
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="batches")
    jobs: Mapped[list["DocumentJob"]] = relationship(
        "DocumentJob", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_batches_owner_status", "owner_id", "status"),)


class DocumentJob(Base, TimestampMixin):
    """Granular execution state for an individual file within a batch."""

    __tablename__ = "document_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=JobStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="jobs")
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="jobs")

    __table_args__ = (
        Index("ix_document_jobs_batch_status", "batch_id", "status"),
        Index("ix_document_jobs_file_status", "file_id", "status"),
    )


class ExtractionRecord(Base):
    """Historical extraction execution output and structured results."""

    __tablename__ = "extraction_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    output_format: Mapped[str] = mapped_column(String(32), nullable=False)
    output_path: Mapped[str] = mapped_column(String(512), nullable=False)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON_TYPE, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="extractions")


class SystemSetting(Base):
    """Platform-level dynamic settings and runtime configuration."""

    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    setting_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    setting_value: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
