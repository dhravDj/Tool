"""Detection result schemas and evidence models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.modules.formats.categories import FormatCategory
from app.modules.formats.support_status import ConfidenceLevel, SupportStatus


class DetectionSignal(StrEnum):
    """Source of detection evidence."""

    MAGIC_SIGNATURE = "magic_signature"
    MIME_DETECTOR = "mime_detector"
    CONTAINER_INSPECTOR = "container_inspector"
    TEXT_PARSER = "text_parser"
    EXTENSION_HINT = "extension_hint"
    SYSTEM_VALIDATOR = "system_validator"


@dataclass
class DetectionEvidence:
    """Individual signal evidence contributed during analysis."""

    signal: DetectionSignal
    format_id: str | None = None
    mime_type: str | None = None
    confidence_score: float = 0.0
    details: str = ""


@dataclass
class AlternativeCandidate:
    """Alternative interpretation when a file is ambiguous or polyglot."""

    format_id: str
    canonical_name: str
    confidence_score: float
    reason: str


@dataclass
class DetectionResult:
    """Consolidated outcome of universal file detection."""

    format_id: str
    canonical_name: str
    display_name: str
    mime_type: str
    extension: str
    claimed_extension: str | None
    category: FormatCategory
    confidence_level: ConfidenceLevel
    confidence_score: float
    support_status: SupportStatus
    is_valid: bool = True
    is_mismatch: bool = False
    is_corrupted: bool = False
    is_suspicious: bool = False
    is_container: bool = False
    container_type: str | None = None
    evidence: list[DetectionEvidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    alternative_candidates: list[AlternativeCandidate] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    file_size: int = 0
    sha256: str = ""
    detection_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result into serializable dictionary."""
        return {
            "format_id": self.format_id,
            "canonical_name": self.canonical_name,
            "display_name": self.display_name,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "claimed_extension": self.claimed_extension,
            "category": self.category.value
            if isinstance(self.category, FormatCategory)
            else str(self.category),
            "confidence_level": self.confidence_level.value,
            "confidence_score": round(self.confidence_score, 4),
            "support_status": self.support_status.value,
            "is_valid": self.is_valid,
            "is_mismatch": self.is_mismatch,
            "is_corrupted": self.is_corrupted,
            "is_suspicious": self.is_suspicious,
            "is_container": self.is_container,
            "container_type": self.container_type,
            "evidence": [
                {
                    "signal": e.signal.value,
                    "format_id": e.format_id,
                    "mime_type": e.mime_type,
                    "confidence_score": e.confidence_score,
                    "details": e.details,
                }
                for e in self.evidence
            ],
            "warnings": self.warnings,
            "alternative_candidates": [
                {
                    "format_id": a.format_id,
                    "canonical_name": a.canonical_name,
                    "confidence_score": a.confidence_score,
                    "reason": a.reason,
                }
                for a in self.alternative_candidates
            ],
            "metadata": self.metadata,
            "file_size": self.file_size,
            "sha256": self.sha256,
            "detection_duration_ms": round(self.detection_duration_ms, 2),
        }
