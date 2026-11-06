"""Step 5: Container format detection."""

from dataclasses import dataclass, field
from pathlib import Path

from app.modules.formats.container_formats import ContainerInspector
from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry


@dataclass
class ContainerDetectionResult:
    """Outcome of container format inspection."""

    is_container: bool
    container_type: str | None = None
    detected_format: FileFormatDefinition | None = None
    manifest_entries: list[str] = field(default_factory=list)
    is_suspicious: bool = False
    is_corrupted: bool = False
    warnings: list[str] = field(default_factory=list)


class ContainerDetector:
    """Dispatches container detection based on raw signatures and inspects internal structures."""

    @classmethod
    def detect_container(
        cls,
        file_path: Path,
        raw_signature_format: FileFormatDefinition | None = None,
    ) -> ContainerDetectionResult:
        # Check if the format is a container
        if not raw_signature_format or not raw_signature_format.is_container:
            # Check by extension hint if it might be an uncompressed or misnamed container
            pass

        container_type = raw_signature_format.container_type if raw_signature_format else None

        # 1. ZIP Containers (DOCX, XLSX, PPTX, ODT, ODS, ODP, EPUB, APK, JAR, ZIP)
        if container_type == "zip" or (
            raw_signature_format and raw_signature_format.format_id == "zip"
        ):
            res = ContainerInspector.inspect_zip_package(file_path)
            fmt = (
                format_registry.get_by_id(res.identified_format_id)
                if res.identified_format_id
                else None
            )
            return ContainerDetectionResult(
                is_container=True,
                container_type="zip",
                detected_format=fmt,
                manifest_entries=res.manifest_entries,
                is_suspicious=res.is_suspicious,
                is_corrupted=res.is_corrupted,
                warnings=res.warnings,
            )

        # 2. RIFF Containers (WEBP, WAV, AVI)
        if container_type == "riff":
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(16)
                res = ContainerInspector.inspect_riff_container(chunk)
                fmt = (
                    format_registry.get_by_id(res.identified_format_id)
                    if res.identified_format_id
                    else None
                )
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="riff",
                    detected_format=fmt,
                    warnings=res.warnings,
                )
            except Exception as e:
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="riff",
                    warnings=[f"Failed reading RIFF container: {e}"],
                )

        # 3. ISO-BMFF Containers (MP4, M4A, MOV, HEIC)
        if container_type == "isobmff":
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(32)
                res = ContainerInspector.inspect_isobmff_container(chunk)
                fmt = (
                    format_registry.get_by_id(res.identified_format_id)
                    if res.identified_format_id
                    else None
                )
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="isobmff",
                    detected_format=fmt,
                    manifest_entries=res.manifest_entries,
                    warnings=res.warnings,
                )
            except Exception as e:
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="isobmff",
                    warnings=[f"Failed reading ISO-BMFF container: {e}"],
                )

        # 4. OLE2 Compound File Containers (DOC, XLS, PPT, MSG)
        if container_type == "ole2":
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(65536)
                res = ContainerInspector.inspect_ole2_container(chunk)
                fmt = (
                    format_registry.get_by_id(res.identified_format_id)
                    if res.identified_format_id
                    else None
                )
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="ole2",
                    detected_format=fmt,
                    manifest_entries=res.manifest_entries,
                    warnings=res.warnings,
                )
            except Exception as e:
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="ole2",
                    warnings=[f"Failed reading OLE2 container: {e}"],
                )

        # 5. EBML Containers (MKV, WEBM)
        if container_type == "ebml" or (
            raw_signature_format and raw_signature_format.format_id in ("mkv", "webm")
        ):
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(512)
                res = ContainerInspector.inspect_ebml_container(chunk)
                fmt = (
                    format_registry.get_by_id(res.identified_format_id)
                    if res.identified_format_id
                    else None
                )
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="ebml",
                    detected_format=fmt,
                    manifest_entries=res.manifest_entries,
                    warnings=res.warnings,
                )
            except Exception as e:
                return ContainerDetectionResult(
                    is_container=True,
                    container_type="ebml",
                    warnings=[f"Failed reading EBML container: {e}"],
                )

        return ContainerDetectionResult(is_container=False)
