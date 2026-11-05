"""Confidence scoring, multi-signal cross-validation, and polyglot evaluation."""

from dataclasses import dataclass

from app.modules.files.detection.detection_result import (
    AlternativeCandidate,
    DetectionEvidence,
    DetectionSignal,
)
from app.modules.formats.categories import FormatCategory
from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry
from app.modules.formats.support_status import ConfidenceLevel, SupportStatus


@dataclass
class EvaluationSynthesis:
    """Outcome of multi-signal arbitration."""

    primary_format: FileFormatDefinition
    confidence_level: ConfidenceLevel
    confidence_score: float
    support_status: SupportStatus
    is_mismatch: bool
    is_corrupted: bool
    is_suspicious: bool
    warnings: list[str]
    alternative_candidates: list[AlternativeCandidate]


class ConfidenceEvaluator:
    """Arbitrates among multiple detection signals to determine the primary format and confidence."""

    @classmethod
    def evaluate(
        cls,
        evidence_list: list[DetectionEvidence],
        claimed_extension: str | None,
        container_format: FileFormatDefinition | None,
        signature_format: FileFormatDefinition | None,
        mime_formats: list[FileFormatDefinition],
        text_format: FileFormatDefinition | None,
        is_corrupted_container: bool = False,
    ) -> EvaluationSynthesis:
        warnings: list[str] = []
        alternatives: list[AlternativeCandidate] = []
        is_mismatch = False
        is_corrupted = is_corrupted_container
        is_suspicious = False

        # 1. Candidate resolution priority:
        # Container > Specific Binary Signature > Text Parser > MIME > Extension Hint
        candidate: FileFormatDefinition | None = None

        if container_format:
            candidate = container_format
        elif signature_format:
            candidate = signature_format
        elif text_format:
            candidate = text_format
        elif mime_formats:
            candidate = mime_formats[0]

        if not candidate:
            candidate = format_registry.get_by_id("unknown") or FileFormatDefinition(
                format_id="unknown",
                canonical_name="Unknown Format",
                display_name="Unidentified File",
                category=FormatCategory.UNKNOWN,
                mime_types=["application/octet-stream"],
                extensions=[],
                support_status=SupportStatus.UNKNOWN_FORMAT,
            )

        # 2. Cross-validation: Check for Extension Mismatch
        if claimed_extension and candidate.format_id != "unknown":
            normalized_claimed = claimed_extension.lower().lstrip(".")
            valid_exts = [e.lower().lstrip(".") for e in candidate.extensions]

            if normalized_claimed not in valid_exts:
                is_mismatch = True
                warnings.append(
                    f"Extension mismatch: filename claims '{claimed_extension}', but binary evidence indicates '{candidate.primary_extension}' ({candidate.canonical_name})."
                )

        # 3. Detect conflicting signals (Polyglot or ambiguity)
        conflicting_signals = set()
        for ev in evidence_list:
            if (
                ev.format_id
                and ev.format_id != candidate.format_id
                and ev.signal != DetectionSignal.EXTENSION_HINT
            ):
                conflicting_signals.add(ev.format_id)
                other = format_registry.get_by_id(ev.format_id)
                if other:
                    alternatives.append(
                        AlternativeCandidate(
                            format_id=other.format_id,
                            canonical_name=other.canonical_name,
                            confidence_score=ev.confidence_score,
                            reason=f"Signaled by {ev.signal.value}: {ev.details}",
                        )
                    )

        if len(conflicting_signals) > 1:
            is_suspicious = True
            warnings.append(
                f"Polyglot / multiple signatures detected: conflicting signals for {', '.join(conflicting_signals)}."
            )

        # 4. Confidence scoring calculation
        # Agreement between signals builds confidence score
        agreeing_signals = 0
        base_score = 0.0

        for ev in evidence_list:
            if ev.format_id == candidate.format_id:
                agreeing_signals += 1
                base_score = max(base_score, ev.confidence_score)

        if container_format and container_format.format_id == candidate.format_id:
            score = 0.98
            conf_level = ConfidenceLevel.HIGH
        elif agreeing_signals >= 2:
            score = min(0.95, base_score + (agreeing_signals - 1) * 0.10)
            conf_level = ConfidenceLevel.HIGH
        elif signature_format and signature_format.format_id == candidate.format_id:
            score = 0.85
            conf_level = ConfidenceLevel.HIGH
        elif text_format and text_format.format_id == candidate.format_id:
            score = base_score
            conf_level = ConfidenceLevel.MEDIUM if score >= 0.75 else ConfidenceLevel.LOW
        elif candidate.format_id == "unknown":
            score = 0.0
            conf_level = ConfidenceLevel.UNKNOWN
        else:
            score = 0.40
            conf_level = ConfidenceLevel.LOW

        # 5. Support Status Resolution
        if is_corrupted:
            support_status = SupportStatus.CORRUPTED_FILE
        elif is_suspicious:
            support_status = SupportStatus.SUSPICIOUS_FILE
        elif len(alternatives) > 1 and conf_level == ConfidenceLevel.LOW:
            support_status = SupportStatus.AMBIGUOUS_FORMAT
        elif candidate.format_id == "unknown":
            support_status = SupportStatus.UNKNOWN_FORMAT
        else:
            support_status = candidate.support_status

        return EvaluationSynthesis(
            primary_format=candidate,
            confidence_level=conf_level,
            confidence_score=score,
            support_status=support_status,
            is_mismatch=is_mismatch,
            is_corrupted=is_corrupted,
            is_suspicious=is_suspicious,
            warnings=warnings,
            alternative_candidates=alternatives,
        )
