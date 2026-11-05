"""Step 3: Binary magic byte detection."""

from dataclasses import dataclass, field
from pathlib import Path

from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry


@dataclass
class SignatureDetectionResult:
    """Outcome of binary signature matching."""

    matched: bool
    primary_format: FileFormatDefinition | None = None
    all_matches: list[FileFormatDefinition] = field(default_factory=list)
    signature_name: str | None = None
    confidence: float = 0.0


class SignatureDetector:
    """Inspects raw byte streams at defined offsets to detect canonical magic numbers."""

    # Read up to 64KB for signatures that reside at higher offsets (e.g. ISO 9660, TAR)
    DEFAULT_BUFFER_SIZE = 65536

    @classmethod
    def detect_signature(cls, file_path: Path) -> SignatureDetectionResult:
        """Read header buffer from disk and match against known signatures."""
        try:
            with open(file_path, "rb") as f:
                header = f.read(cls.DEFAULT_BUFFER_SIZE)
        except Exception:
            return SignatureDetectionResult(matched=False)

        if not header:
            return SignatureDetectionResult(matched=False)

        matches = format_registry.find_by_signature(header)
        if not matches:
            return SignatureDetectionResult(matched=False)

        # Primary match (first registered, or most specific)
        primary = matches[0]
        sig_name = primary.magic_signatures[0].name if primary.magic_signatures else "MAGIC"

        return SignatureDetectionResult(
            matched=True,
            primary_format=primary,
            all_matches=matches,
            signature_name=sig_name,
            confidence=0.95,
        )
