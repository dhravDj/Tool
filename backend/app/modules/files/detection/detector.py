"""Universal File Detection Pipeline coordinating all detection steps."""

import time
from pathlib import Path
from typing import Any

from app.modules.files.detection.confidence import ConfidenceEvaluator
from app.modules.files.detection.container_detector import ContainerDetector
from app.modules.files.detection.detection_result import (
    DetectionEvidence,
    DetectionResult,
    DetectionSignal,
)
from app.modules.files.detection.extension_detector import ExtensionDetector
from app.modules.files.detection.metadata import SafeMetadataExtractor
from app.modules.files.detection.mime_detector import MimeDetector
from app.modules.files.detection.signature_detector import SignatureDetector
from app.modules.files.detection.text_detector import TextDetector
from app.modules.files.detection.validation import FileValidator
from app.modules.formats.categories import FormatCategory
from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry
from app.modules.formats.support_status import ConfidenceLevel, SupportStatus
from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.detector import DetectionResult as PluginDetectionResult
from app.plugins.interfaces.detector import FileDetectorInterface


class UniversalFileDetector(FileDetectorInterface):
    """Production-grade multi-signal file detection engine."""

    ENGINE_VERSION: str = "2.0.0"

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="universal_file_detector",
            version="2.0.0",
            description="Universal multi-signal file format and MIME detection engine.",
            plugin_type=PluginType.DETECTOR,
            supported_formats=["*"],
            required_dependencies=["python-magic", "libmagic"],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        return True

    async def detect(
        self,
        file_path: Path,
        original_filename: str | None = None,
    ) -> PluginDetectionResult:
        """Compatibility method for FileDetectorInterface."""
        result = self.detect_file(file_path, original_filename)
        return PluginDetectionResult(
            mime_type=result.mime_type,
            extension=result.extension,
            category=result.category,
            confidence=result.confidence_score,
            detected_by=self.metadata.name,
            encoding=result.metadata.get("encoding"),
        )

    def detect_file(
        self,
        file_path: Path,
        original_filename: str | None = None,
    ) -> DetectionResult:
        """Run the complete 7-step universal file detection pipeline."""
        start_time = time.perf_counter()
        effective_filename = original_filename or file_path.name
        evidence_list: list[DetectionEvidence] = []
        warnings: list[str] = []

        # ----------------------------------------------------------------------
        # STEP 1: Basic File Validation
        # ----------------------------------------------------------------------
        val_res = FileValidator.validate_file(file_path)
        if not val_res.is_valid:
            duration = (time.perf_counter() - start_time) * 1000
            status = SupportStatus.INVALID_FILE
            if val_res.is_empty:
                status = SupportStatus.CORRUPTED_FILE
            return DetectionResult(
                format_id="invalid",
                canonical_name="Invalid or Unreadable File",
                display_name="Invalid File",
                mime_type="application/octet-stream",
                extension="",
                claimed_extension=file_path.suffix.lstrip(".") or None,
                category=FormatCategory.UNKNOWN,
                confidence_level=ConfidenceLevel.UNKNOWN,
                confidence_score=0.0,
                support_status=status,
                is_valid=False,
                warnings=[val_res.error_message or "File validation failed."],
                detection_duration_ms=duration,
            )

        file_size = val_res.file_size

        # ----------------------------------------------------------------------
        # STEP 2: Extension Analysis
        # ----------------------------------------------------------------------
        ext_res = ExtensionDetector.analyze(effective_filename)
        if ext_res.has_extension:
            for cand in ext_res.candidate_formats:
                evidence_list.append(
                    DetectionEvidence(
                        signal=DetectionSignal.EXTENSION_HINT,
                        format_id=cand.format_id,
                        mime_type=cand.primary_mime,
                        confidence_score=0.25,
                        details=f"Filename extension matches .{ext_res.claimed_extension}",
                    )
                )

        # ----------------------------------------------------------------------
        # STEP 3: Magic Byte Detection
        # ----------------------------------------------------------------------
        sig_res = SignatureDetector.detect_signature(file_path)
        sig_format: FileFormatDefinition | None = None
        if sig_res.matched and sig_res.primary_format:
            sig_format = sig_res.primary_format
            evidence_list.append(
                DetectionEvidence(
                    signal=DetectionSignal.MAGIC_SIGNATURE,
                    format_id=sig_format.format_id,
                    mime_type=sig_format.primary_mime,
                    confidence_score=sig_res.confidence,
                    details=f"Matched magic byte signature '{sig_res.signature_name}'",
                )
            )

        # ----------------------------------------------------------------------
        # STEP 4: MIME Detection (libmagic / fallback)
        # ----------------------------------------------------------------------
        mime_res = MimeDetector.detect_mime(file_path)
        mime_formats = format_registry.get_by_mime(mime_res.mime_type)
        if mime_formats:
            evidence_list.append(
                DetectionEvidence(
                    signal=DetectionSignal.MIME_DETECTOR,
                    format_id=mime_formats[0].format_id,
                    mime_type=mime_res.mime_type,
                    confidence_score=0.75 if mime_res.detection_method == "libmagic" else 0.40,
                    details=f"Detected by {mime_res.detection_method}: {mime_res.mime_type}",
                )
            )
        warnings.extend(mime_res.warnings)

        # ----------------------------------------------------------------------
        # STEP 5: Container Inspection
        # ----------------------------------------------------------------------
        container_res = ContainerDetector.detect_container(file_path, sig_format)
        container_format: FileFormatDefinition | None = None
        if container_res.is_container and container_res.detected_format:
            container_format = container_res.detected_format
            evidence_list.append(
                DetectionEvidence(
                    signal=DetectionSignal.CONTAINER_INSPECTOR,
                    format_id=container_format.format_id,
                    mime_type=container_format.primary_mime,
                    confidence_score=0.98,
                    details=f"Container ({container_res.container_type}) verified manifest: {', '.join(container_res.manifest_entries[:3])}",
                )
            )
        warnings.extend(container_res.warnings)

        # ----------------------------------------------------------------------
        # STEP 6: Text Format Heuristics (if not identified by binary signature)
        # ----------------------------------------------------------------------
        text_format: FileFormatDefinition | None = None
        if not sig_res.matched and not container_res.is_container:
            text_res = TextDetector.analyze_text(file_path, ext_res.normalized_extension)
            if text_res.is_text and text_res.detected_format:
                text_format = text_res.detected_format
                evidence_list.append(
                    DetectionEvidence(
                        signal=DetectionSignal.TEXT_PARSER,
                        format_id=text_format.format_id,
                        mime_type=text_format.primary_mime,
                        confidence_score=text_res.confidence,
                        details=f"Text heuristics matched syntax '{text_res.structure_type}' (encoding: {text_res.encoding})",
                    )
                )

        # Corruption & truncation validation
        is_corrupted = container_res.is_corrupted
        if sig_format:
            if sig_format.format_id == "pdf":
                try:
                    with open(file_path, "rb") as f:
                        if file_size < 32:
                            is_corrupted = True
                            warnings.append(
                                "Truncated PDF: file size smaller than minimal PDF header/trailer bounds."
                            )
                        else:
                            f.seek(max(0, file_size - 1024))
                            tail = f.read(1024)
                            if b"%%EOF" not in tail:
                                is_corrupted = True
                                warnings.append(
                                    "Truncated or corrupted PDF: missing %%EOF trailer terminator."
                                )
                except Exception:
                    pass
            elif sig_format.format_id == "png":
                try:
                    with open(file_path, "rb") as f:
                        if file_size < 33:
                            is_corrupted = True
                            warnings.append(
                                "Truncated PNG: file size smaller than minimal PNG structure."
                            )
                        else:
                            f.seek(max(0, file_size - 32))
                            tail = f.read(32)
                            if b"IEND" not in tail:
                                is_corrupted = True
                                warnings.append("Truncated PNG: missing IEND chunk.")
                except Exception:
                    pass
            elif sig_format.format_id in ("jpeg", "jpg"):
                try:
                    with open(file_path, "rb") as f:
                        if file_size < 64:
                            is_corrupted = True
                        else:
                            f.seek(max(0, file_size - 16))
                            tail = f.read(16)
                            if b"\xff\xd9" not in tail:
                                is_corrupted = True
                                warnings.append(
                                    "Truncated JPEG: missing EOI (End of Image) marker."
                                )
                except Exception:
                    pass

        # ----------------------------------------------------------------------
        # STEP 7: Cross-Validation, Confidence Arbitration & Metadata
        # ----------------------------------------------------------------------
        synthesis = ConfidenceEvaluator.evaluate(
            evidence_list=evidence_list,
            claimed_extension=ext_res.claimed_extension,
            container_format=container_format,
            signature_format=sig_format,
            mime_formats=mime_formats,
            text_format=text_format,
            is_corrupted_container=is_corrupted,
        )
        warnings.extend(synthesis.warnings)

        # Metadata extraction
        metadata = SafeMetadataExtractor.extract_metadata(
            file_path=file_path,
            format_id=synthesis.primary_format.format_id,
            category=synthesis.primary_format.category.value,
            mime_type=synthesis.primary_format.primary_mime,
            original_filename=effective_filename,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return DetectionResult(
            format_id=synthesis.primary_format.format_id,
            canonical_name=synthesis.primary_format.canonical_name,
            display_name=synthesis.primary_format.display_name,
            mime_type=synthesis.primary_format.primary_mime,
            extension=synthesis.primary_format.primary_extension,
            claimed_extension=ext_res.claimed_extension,
            category=synthesis.primary_format.category,
            confidence_level=synthesis.confidence_level,
            confidence_score=synthesis.confidence_score,
            support_status=synthesis.support_status,
            is_valid=True,
            is_mismatch=synthesis.is_mismatch,
            is_corrupted=synthesis.is_corrupted,
            is_suspicious=synthesis.is_suspicious,
            is_container=container_res.is_container,
            container_type=container_res.container_type,
            evidence=evidence_list,
            warnings=warnings,
            alternative_candidates=synthesis.alternative_candidates,
            metadata=metadata,
            file_size=file_size,
            sha256=metadata.get("sha256", ""),
            detection_duration_ms=duration_ms,
        )


# Global singleton detector instance
universal_detector = UniversalFileDetector()
