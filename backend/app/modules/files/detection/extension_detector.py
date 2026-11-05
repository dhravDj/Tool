"""Step 2: Extension normalization and analysis."""

from dataclasses import dataclass
from pathlib import Path

from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry


@dataclass
class ExtensionAnalysisResult:
    """Outcome of extension inspection."""

    claimed_extension: str | None
    has_extension: bool
    candidate_formats: list[FileFormatDefinition]
    normalized_extension: str | None


class ExtensionDetector:
    """Extracts and normalizes filename extensions, resolving matching registry formats."""

    # Multi-part compound extensions to check before single suffix
    COMPOUND_EXTENSIONS = {
        "tar.gz": "gz",
        "tar.bz2": "bz2",
        "tar.xz": "xz",
        "tar.zst": "tar",
    }

    @classmethod
    def analyze(cls, filename: str) -> ExtensionAnalysisResult:
        if not filename:
            return ExtensionAnalysisResult(
                claimed_extension=None,
                has_extension=False,
                candidate_formats=[],
                normalized_extension=None,
            )

        name_lower = filename.lower().strip()

        # Check compound extensions first
        for compound, alias in cls.COMPOUND_EXTENSIONS.items():
            if name_lower.endswith(f".{compound}"):
                matched_formats = format_registry.get_by_extension(alias)
                return ExtensionAnalysisResult(
                    claimed_extension=compound,
                    has_extension=True,
                    candidate_formats=matched_formats,
                    normalized_extension=alias,
                )

        # Standard single extension extraction
        path = Path(name_lower)
        ext = path.suffix.lstrip(".")

        if not ext:
            return ExtensionAnalysisResult(
                claimed_extension=None,
                has_extension=False,
                candidate_formats=[],
                normalized_extension=None,
            )

        matched_formats = format_registry.get_by_extension(ext)
        return ExtensionAnalysisResult(
            claimed_extension=ext,
            has_extension=True,
            candidate_formats=matched_formats,
            normalized_extension=ext,
        )
