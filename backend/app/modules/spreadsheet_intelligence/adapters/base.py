"""Abstract base adapter for spreadsheet intelligence extraction."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
)

logger = logging.getLogger(__name__)


class SpreadsheetLimitsExceededError(Exception):
    """Raised when worksheet dimensions exceed configured security ceilings."""
    pass


class BaseSpreadsheetAdapter(ABC):
    """Base interface for format-specific spreadsheet parsing engines."""

    format_id: str
    engine_name: str
    version: str = "1.0.0"

    def __init__(
        self,
        max_rows: int = 1_000_000,
        max_columns: int = 16_384,
        max_cells: int = 10_000_000,
    ) -> None:
        self.max_rows = max_rows
        self.max_columns = max_columns
        self.max_cells = max_cells

    @abstractmethod
    def extract_workbook(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> SpreadsheetDocument:
        """Extract canonical spreadsheet structure, sheets, cells, and metadata."""
        pass

    def check_limits(self, row_count: int, col_count: int) -> None:
        """Enforce DOS and memory protection bounds."""
        if row_count > self.max_rows:
            raise SpreadsheetLimitsExceededError(
                f"Worksheet row count ({row_count:,}) exceeds maximum permitted limit ({self.max_rows:,})."
            )
        if col_count > self.max_columns:
            raise SpreadsheetLimitsExceededError(
                f"Worksheet column count ({col_count:,}) exceeds maximum permitted limit ({self.max_columns:,})."
            )
        total_cells = row_count * col_count
        if total_cells > self.max_cells:
            raise SpreadsheetLimitsExceededError(
                f"Worksheet cell capacity ({total_cells:,}) exceeds safety ceiling ({self.max_cells:,})."
            )
