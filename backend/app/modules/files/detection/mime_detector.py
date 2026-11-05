"""Step 4: MIME type detection using libmagic with fallback."""

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import logger

try:
    import magic  # python-magic ctypes binding for libmagic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


@dataclass
class MimeDetectionResult:
    """Outcome of MIME inspection."""

    mime_type: str
    detection_method: str  # "libmagic", "pure_python_guess", "fallback"
    encoding: str | None = None
    warnings: list[str] = field(default_factory=list)


class MimeDetector:
    """Determines MIME types using libmagic binary analysis with defensive fallbacks."""

    @classmethod
    def detect_mime(cls, file_path: Path) -> MimeDetectionResult:
        warnings = []

        if HAS_MAGIC:
            try:
                # 1. Use python-magic to inspect file content directly
                detected_mime = magic.from_file(str(file_path), mime=True)
                detected_encoding = None
                try:
                    encoding_magic = magic.Magic(mime_encoding=True)
                    detected_encoding = encoding_magic.from_file(str(file_path))
                except Exception:
                    pass

                if detected_mime:
                    return MimeDetectionResult(
                        mime_type=detected_mime.strip().lower(),
                        detection_method="libmagic",
                        encoding=detected_encoding,
                    )
            except Exception as e:
                warnings.append(f"libmagic inspection error: {e}")
                logger.warning(f"libmagic failed on {file_path.name}: {e}")

        # 2. Pure python fallback using mimetypes guessing
        guessed, enc = mimetypes.guess_type(str(file_path))
        if guessed:
            warnings.append(
                "MIME guessed from file extension as libmagic was unavailable or failed."
            )
            return MimeDetectionResult(
                mime_type=guessed.lower(),
                detection_method="pure_python_guess",
                encoding=enc,
                warnings=warnings,
            )

        # 3. Default fallback
        return MimeDetectionResult(
            mime_type="application/octet-stream",
            detection_method="fallback",
            warnings=warnings
            or ["Could not determine MIME type, defaulted to application/octet-stream."],
        )
