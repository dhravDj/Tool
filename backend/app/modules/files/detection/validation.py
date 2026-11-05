"""Step 1: Basic file system validity and boundary validation."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings


@dataclass
class FileValidationResult:
    """Outcome of initial filesystem safety checks."""

    is_valid: bool
    is_empty: bool = False
    is_too_large: bool = False
    is_special_device: bool = False
    file_size: int = 0
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)


class FileValidator:
    """Performs defensive validation on input file paths before inspecting content."""

    @classmethod
    def validate_file(cls, file_path: Path) -> FileValidationResult:
        # 1. Existence check
        if not file_path.exists():
            return FileValidationResult(
                is_valid=False,
                error_message=f"File does not exist: {file_path.name}",
            )

        # 2. Symlink & special device security
        try:
            stat_res = file_path.stat()
        except OSError as e:
            return FileValidationResult(
                is_valid=False,
                error_message=f"Cannot stat file (permission or I/O error): {e}",
            )

        if not file_path.is_file():
            return FileValidationResult(
                is_valid=False,
                is_special_device=True,
                error_message="Path is not a regular file (directory, FIFO, socket, or device node).",
            )

        # Check for broken symlinks
        if file_path.is_symlink() and not file_path.resolve().exists():
            return FileValidationResult(
                is_valid=False,
                error_message="Dangling or broken symbolic link.",
            )

        file_size = stat_res.st_size

        # 3. Empty file check
        if file_size == 0:
            return FileValidationResult(
                is_valid=False,
                is_empty=True,
                file_size=0,
                error_message="File is zero bytes (empty).",
            )

        # 4. Maximum size limit check
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return FileValidationResult(
                is_valid=False,
                is_too_large=True,
                file_size=file_size,
                error_message=f"File size ({actual_mb:.2f} MB) exceeds maximum allowed limit ({max_mb:.0f} MB).",
            )

        # 5. Readability check
        if not os.access(file_path, os.R_OK):
            return FileValidationResult(
                is_valid=False,
                file_size=file_size,
                error_message="File is not readable (insufficient filesystem permissions).",
            )

        return FileValidationResult(
            is_valid=True,
            file_size=file_size,
        )
