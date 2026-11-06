"""SQLAlchemy 2.0 declarative database models."""

import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
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
    # Phase 2: Universal File Detection metadata
    detection_format_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    claimed_extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    format_category: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    support_status: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_mismatch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_corrupted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detection_evidence: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE, default=dict, nullable=False
    )
    detection_warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    file_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    detection_engine_version: Mapped[str | None] = mapped_column(
        String(32), default="2.0.0", nullable=True
    )
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    image_analyses: Mapped[list["ImageAnalysisRecord"]] = relationship(
        "ImageAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    spreadsheet_analyses: Mapped[list["SpreadsheetAnalysisRecord"]] = relationship(
        "SpreadsheetAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    presentation_analyses: Mapped[list["PresentationAnalysisRecord"]] = relationship(
        "PresentationAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    audio_analyses: Mapped[list["AudioAnalysisRecord"]] = relationship(
        "AudioAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    video_analyses: Mapped[list["VideoAnalysisRecord"]] = relationship(
        "VideoAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
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


class ImageAnalysisRecord(Base):
    """Historical image intelligence analysis execution record and visual findings."""

    __tablename__ = "image_analysis_records"

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
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    color_mode: Mapped[str] = mapped_column(String(32), default="RGB", nullable=False)
    has_transparency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_animated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ocr_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_objects_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_charts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_diagrams: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    analysis_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON_TYPE, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="image_analyses")


class SpreadsheetAnalysisRecord(Base):
    """Historical spreadsheet intelligence analysis record and workbook findings."""

    __tablename__ = "spreadsheet_analysis_records"

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
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    sheet_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_columns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cells: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    formula_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_charts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_tables: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_merged_cells: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_hidden_sheets: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    workbook_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    profiling_summary: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="spreadsheet_analyses")


class PresentationAnalysisRecord(Base):
    """Historical presentation intelligence analysis record and slide findings."""

    __tablename__ = "presentation_analysis_records"

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
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    slide_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hidden_slide_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_elements: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_notes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_tables: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_charts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_diagrams: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    presentation_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), default="6.0.0", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="presentation_analyses")


class AudioAnalysisRecord(Base):
    """Historical audio intelligence analysis record and speech-to-text findings."""

    __tablename__ = "audio_analysis_records"

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
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    channels: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    codec: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    full_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    speaker_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    segment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_diarization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_word_timestamps: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_events: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), default="documind-acoustic-v1", nullable=False)
    engine_name: Mapped[str] = mapped_column(String(64), default="documind-acoustic", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    audio_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="audio_analyses")


class VideoAnalysisRecord(Base):
    """Historical video intelligence analysis record, scenes, keyframes, and multimodal findings."""

    __tablename__ = "video_analysis_records"

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
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    video_codec: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    audio_codec: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    scene_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keyframe_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    track_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), default="documind-video-v1", nullable=False)
    engine_name: Mapped[str] = mapped_column(String(64), default="documind-video", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    video_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="video_analyses")



