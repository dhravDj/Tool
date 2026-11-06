"""Optional Apache Parquet exporter for suitable tabular worksheet datasets."""

import io
from pathlib import Path
from typing import Any

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    WorksheetData,
)


class SpreadsheetParquetExporter:
    """Exports structured tabular worksheet data to Apache Parquet format if pyarrow is installed."""

    @staticmethod
    def is_available() -> bool:
        try:
            import pyarrow  # type: ignore[import-untyped,import-not-found] # noqa: F401
            import pyarrow.parquet  # type: ignore[import-untyped,import-not-found] # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def export_sheet_parquet(
        cls,
        worksheet: WorksheetData,
        output_path: Path | None = None,
    ) -> bytes | None:
        """Convert a worksheet's tabular grid into Apache Parquet binary bytes."""
        if not cls.is_available():
            return None

        import pyarrow as pa  # type: ignore[import-untyped,import-not-found]
        import pyarrow.parquet as pq  # type: ignore[import-untyped,import-not-found]

        if not worksheet.rows or len(worksheet.rows) < 2:
            return None

        # Row 1 is headers
        headers = [col.name or f"Col_{col.column_index}" for col in worksheet.columns]
        if not headers:
            headers = [f"Col_{i+1}" for i in range(worksheet.total_columns)]

        # Collect column arrays
        col_arrays: dict[str, list[Any]] = {h: [] for h in headers}

        for row in worksheet.rows[1:]:  # Skip header row
            cells_map = {c.column: c.raw_value for c in row.cells}
            for idx, h in enumerate(headers, start=1):
                val = cells_map.get(idx)
                # Convert values to strings or primitives
                if isinstance(val, (int, float, bool, str)) or val is None:
                    col_arrays[h].append(val)
                else:
                    col_arrays[h].append(str(val))

        try:
            table = pa.Table.from_pydict(col_arrays)
            buf = io.BytesIO()
            pq.write_table(table, buf, compression="snappy")
            data = buf.getvalue()
            if output_path:
                output_path.write_bytes(data)
            return data
        except Exception:
            return None
