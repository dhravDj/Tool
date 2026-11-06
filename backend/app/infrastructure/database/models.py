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
    processing_batches: Mapped[list["ProcessingBatchRecord"]] = relationship(
        "ProcessingBatchRecord", back_populates="owner", cascade="all, delete-orphan"
    )


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
    code_analyses: Mapped[list["CodeAnalysisRecord"]] = relationship(
        "CodeAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    structured_data_analyses: Mapped[list["StructuredDataAnalysisRecord"]] = relationship(
        "StructuredDataAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    archive_analyses: Mapped[list["ArchiveAnalysisRecord"]] = relationship(
        "ArchiveAnalysisRecord", back_populates="file", cascade="all, delete-orphan"
    )
    knowledge_documents: Mapped[list["KnowledgeDocumentRecord"]] = relationship(
        "KnowledgeDocumentRecord", back_populates="file", cascade="all, delete-orphan"
    )
    knowledge_chunks: Mapped[list["KnowledgeChunkRecord"]] = relationship(
        "KnowledgeChunkRecord", back_populates="file", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["SummaryRecord"]] = relationship(
        "SummaryRecord", back_populates="file", cascade="all, delete-orphan"
    )
    batch_files: Mapped[list["BatchFileRecord"]] = relationship(
        "BatchFileRecord", back_populates="file", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[list["ProcessingJobRecord"]] = relationship(
        "ProcessingJobRecord", back_populates="file", cascade="all, delete-orphan"
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


class CodeAnalysisRecord(Base):
    """Historical code intelligence analysis record, AST parsing, symbols, metrics, and diagnostics."""

    __tablename__ = "code_analysis_records"

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
    language: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    code_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blank_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    symbol_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    function_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    class_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    import_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    diagnostic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_syntax_errors: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cyclomatic_complexity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), default="documind-code-v1", nullable=False)
    engine_name: Mapped[str] = mapped_column(String(64), default="documind-code", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    code_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="code_analyses")


class StructuredDataAnalysisRecord(Base):
    """Historical structured data intelligence analysis record, schema inference, data profiling."""

    __tablename__ = "structured_data_analysis_records"

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
    root_type: Mapped[str] = mapped_column(String(32), default="object", nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    field_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    compression: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), default="documind-structured-v1", nullable=False)
    engine_name: Mapped[str] = mapped_column(String(64), default="documind-structured", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    schema_definition: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    profile_data: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="structured_data_analyses")


class ArchiveAnalysisRecord(Base):
    """Historical archive inspection, extraction, and nested hierarchy record."""

    __tablename__ = "archive_analysis_records"

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
    archive_format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    processing_mode: Mapped[str] = mapped_column(String(32), default="inspect_only", nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    directory_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nested_archive_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_uncompressed_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    extracted_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    compression_ratio: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    nesting_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_corrupted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archive_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(64), default="documind-archive-v1", nullable=False)
    engine_name: Mapped[str] = mapped_column(String(64), default="documind-archive", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    processing_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    safety_report: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    artifacts: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    archive_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="archive_analyses")
    entries: Mapped[list["ArchiveEntryRecord"]] = relationship(
        "ArchiveEntryRecord", back_populates="archive_analysis", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["ArchiveRelationshipRecord"]] = relationship(
        "ArchiveRelationshipRecord",
        foreign_keys="ArchiveRelationshipRecord.parent_archive_id",
        back_populates="parent_archive",
        cascade="all, delete-orphan",
    )


class ArchiveEntryRecord(Base):
    """Individual archive entry record preserving metadata, checksums, and extraction linkages."""

    __tablename__ = "archive_entry_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    archive_analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("archive_analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_path: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    extension: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), default="file", nullable=False)
    compressed_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    uncompressed_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    compression_method: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_directory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_symlink: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_nested_archive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detection_result: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    extracted_file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    processing_status: Mapped[str] = mapped_column(String(32), default="inspected", index=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    archive_analysis: Mapped["ArchiveAnalysisRecord"] = relationship(
        "ArchiveAnalysisRecord", back_populates="entries"
    )
    extracted_file: Mapped[Optional["FileRecord"]] = relationship(
        "FileRecord", foreign_keys=[extracted_file_id]
    )


class ArchiveRelationshipRecord(Base):
    """Parent-child hierarchy and provenance linkage for nested archives and extracted child files."""

    __tablename__ = "archive_relationship_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    parent_file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_archive_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("archive_analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_entry_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    child_file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    root_archive_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("archive_analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nesting_depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_storage_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detection_result: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="extracted", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    parent_file: Mapped["FileRecord"] = relationship("FileRecord", foreign_keys=[parent_file_id])
    parent_archive: Mapped["ArchiveAnalysisRecord"] = relationship(
        "ArchiveAnalysisRecord", foreign_keys=[parent_archive_id], back_populates="relationships"
    )
    child_file: Mapped["FileRecord"] = relationship("FileRecord", foreign_keys=[child_file_id])
    root_archive: Mapped["ArchiveAnalysisRecord"] = relationship(
        "ArchiveAnalysisRecord", foreign_keys=[root_archive_id]
    )


# =============================================================================
# Phase 11 — Universal AI Intelligence Engine Models
# =============================================================================


class KnowledgeDocumentRecord(Base, TimestampMixin):
    """Universal normalized knowledge document extracted from any file modality."""

    __tablename__ = "knowledge_documents"

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
    knowledge_document_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    total_blocks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="knowledge_documents")
    chunks: Mapped[list["KnowledgeChunkRecord"]] = relationship(
        "KnowledgeChunkRecord", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunkRecord(Base):
    """Searchable, chunked content unit with exact source references and embedding status."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    knowledge_document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source_reference: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    embedding_status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True, nullable=False
    )
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    document: Mapped["KnowledgeDocumentRecord"] = relationship(
        "KnowledgeDocumentRecord", back_populates="chunks"
    )
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="knowledge_chunks")
    embedding: Mapped[Optional["EmbeddingRecord"]] = relationship(
        "EmbeddingRecord", back_populates="chunk", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_chunks_file_index", "file_id", "chunk_index"),
        Index("ix_chunks_doc_index", "knowledge_document_id", "chunk_index"),
    )


class EmbeddingRecord(Base):
    """Vector embedding representation for a knowledge chunk."""

    __tablename__ = "embedding_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_chunks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_data: Mapped[list[float]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    chunk: Mapped["KnowledgeChunkRecord"] = relationship(
        "KnowledgeChunkRecord", back_populates="embedding"
    )


class AIConversationRecord(Base, TimestampMixin):
    """Multi-turn conversation session tied to files or global workspace."""

    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="sovereign", nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(64), default="documind-sovereign-llm-v1", nullable=False
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    context_mode: Mapped[str] = mapped_column(String(32), default="single_file", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)

    # Relationships
    file: Mapped[Optional["FileRecord"]] = relationship("FileRecord")
    messages: Mapped[list["AIMessageRecord"]] = relationship(
        "AIMessageRecord",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessageRecord.created_at",
    )


class AIMessageRecord(Base):
    """Individual user or AI assistant turn within an AI conversation."""

    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    thought_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_TYPE, default=list, nullable=False
    )
    retrieval_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retrieval_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["AIConversationRecord"] = relationship(
        "AIConversationRecord", back_populates="messages"
    )
    retrieval: Mapped[Optional["RetrievalRecord"]] = relationship("RetrievalRecord")


class RetrievalRecord(Base):
    """Audit log of RAG retrieval queries, scores, and retrieved chunk hits."""

    __tablename__ = "retrieval_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    search_mode: Mapped[str] = mapped_column(String(32), default="hybrid", nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    filter_payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    hits_payload: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_TYPE, default=list, nullable=False
    )
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class AIProviderConfigRecord(Base):
    """Configuration, credentials, and user consent status for AI providers."""

    __tablename__ = "ai_provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider_name: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_model: Mapped[str] = mapped_column(String(64), nullable=False)
    user_consent_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settings_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE, default=dict, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AIUsageRecord(Base):
    """Usage tracking and token telemetry for AI and RAG operations."""

    __tablename__ = "ai_usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class SummaryRecord(Base):
    """Pre-computed and cached multi-type file summaries."""

    __tablename__ = "summary_records"

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
    summary_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_TYPE, default=list, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="summaries")

    __table_args__ = (
        Index("ix_summaries_file_type", "file_id", "summary_type"),
    )


class ProcessingBatchRecord(Base):
    """Large-scale bulk processing batch record tracking thousands of files."""

    __tablename__ = "processing_batches"

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
    accepted_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queued_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    partially_completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
        nullable=False,
    )
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    processing_policy: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE, default=dict, nullable=False
    )
    error_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE, default=dict, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="processing_batches")
    files: Mapped[list["BatchFileRecord"]] = relationship(
        "BatchFileRecord", back_populates="batch", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["ProcessingJobRecord"]] = relationship(
        "ProcessingJobRecord", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_processing_batches_owner_status", "owner_id", "status"),
        Index("ix_processing_batches_created_at", "created_at"),
    )


class BatchFileRecord(Base):
    """File item tracked within a large processing batch."""

    __tablename__ = "batch_files"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default="accepted",
        index=True,
        nullable=False,
    )
    validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedup_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    batch: Mapped["ProcessingBatchRecord"] = relationship("ProcessingBatchRecord", back_populates="files")
    file: Mapped[Optional["FileRecord"]] = relationship("FileRecord", back_populates="batch_files")
    jobs: Mapped[list["ProcessingJobRecord"]] = relationship(
        "ProcessingJobRecord", back_populates="batch_file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_batch_files_batch_status", "batch_id", "status"),
        Index("ix_batch_files_sha256", "sha256"),
    )


class ProcessingJobRecord(Base):
    """Job tracking pipeline execution across detection, extraction, and AI indexing."""

    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    batch_file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batch_files.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(64), default="pipeline_orchestration", index=True, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(64), default="queued", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        index=True,
        nullable=False,
    )
    current_worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stage_progress: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    batch: Mapped[Optional["ProcessingBatchRecord"]] = relationship(
        "ProcessingBatchRecord", back_populates="jobs"
    )
    batch_file: Mapped[Optional["BatchFileRecord"]] = relationship(
        "BatchFileRecord", back_populates="jobs"
    )
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="processing_jobs")
    attempts: Mapped[list["JobAttemptRecord"]] = relationship(
        "JobAttemptRecord", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_processing_jobs_batch_status", "batch_id", "status"),
        Index("ix_processing_jobs_priority_status", "priority", "status"),
        Index("ix_processing_jobs_file_stage", "file_id", "stage"),
    )


class JobAttemptRecord(Base):
    """Detailed audit attempt of a processing job execution."""

    __tablename__ = "job_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_peak_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    job: Mapped["ProcessingJobRecord"] = relationship("ProcessingJobRecord", back_populates="attempts")

    __table_args__ = (
        Index("ix_job_attempts_job_attempt", "job_id", "attempt_number"),
    )


class WorkerHeartbeatRecord(Base):
    """Active worker node heartbeat and resource telemetry."""

    __tablename__ = "worker_heartbeats"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    worker_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_type: Mapped[str] = mapped_column(String(64), default="generic", nullable=False)
    current_job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    memory_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gpu_utilization: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_memory_used_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="alive", index=True, nullable=False)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        index=True,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )






