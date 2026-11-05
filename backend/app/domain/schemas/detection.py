"""Pydantic schemas for file detection API requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


class DetectionEvidenceSchema(BaseModel):
    signal: str
    format_id: str | None = None
    mime_type: str | None = None
    confidence_score: float
    details: str


class AlternativeCandidateSchema(BaseModel):
    format_id: str
    canonical_name: str
    confidence_score: float
    reason: str


class DetectionResultSchema(BaseModel):
    """Complete detection result representation returned to API consumers."""

    format_id: str
    canonical_name: str
    display_name: str
    mime_type: str
    extension: str
    claimed_extension: str | None = None
    category: str
    confidence_level: str
    confidence_score: float
    support_status: str
    is_valid: bool
    is_mismatch: bool
    is_corrupted: bool
    is_suspicious: bool
    is_container: bool
    container_type: str | None = None
    evidence: list[DetectionEvidenceSchema] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    alternative_candidates: list[AlternativeCandidateSchema] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_size: int
    sha256: str
    detection_duration_ms: float
    persisted_file_id: str | None = None


class BatchDetectionResponse(BaseModel):
    total_files: int
    successful_detections: int
    mismatched_extensions: int
    suspicious_files: int
    results: list[DetectionResultSchema]


class FormatDetailSchema(BaseModel):
    format_id: str
    canonical_name: str
    display_name: str
    category: str
    mime_types: list[str]
    extensions: list[str]
    is_container: bool
    container_type: str | None = None
    support_status: str
    extraction_plugin_id: str | None = None
    version_info: str | None = None
    description: str


class FormatListResponse(BaseModel):
    total_formats: int
    formats: list[FormatDetailSchema]


class DetectionCapabilitiesResponse(BaseModel):
    engine_name: str = "UniversalFileDetector"
    version: str = "2.0.0"
    libmagic_available: bool
    total_registered_formats: int
    supported_categories: list[str]
    max_upload_size_bytes: int
    max_upload_size_mb: float
    active_detection_layers: list[str]
