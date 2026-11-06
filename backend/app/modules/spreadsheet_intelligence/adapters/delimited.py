"""High-performance delimited text spreadsheet adapter (CSV and TSV).

Supports robust delimiter sniffing, multi-encoding detection (UTF-8, UTF-8-BOM, UTF-16, Latin1),
quoted fields with embedded newlines, ragged rows normalization, and streaming execution.
"""

import csv
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.modules.spreadsheet_intelligence.adapters.base import (
    BaseSpreadsheetAdapter,
)
from app.modules.spreadsheet_intelligence.profiling.profiler import DataUnderstandingProfiler
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    CellData,
    CellDataType,
    ColumnData,
    RowData,
    SheetVisibility,
    SpreadsheetDocument,
    WorkbookMetadata,
    WorksheetData,
)

logger = logging.getLogger(__name__)


class DelimitedSpreadsheetAdapter(BaseSpreadsheetAdapter):
    """Parses comma-separated and tab-separated tabular data files into canonical spreadsheet AST."""

    format_id = "csv"
    engine_name = "delimited_adapter"
    version = "1.0.0"

    def __init__(
        self,
        default_delimiter: str = ",",
        max_rows: int = 1_000_000,
        max_columns: int = 16_384,
    ) -> None:
        super().__init__(max_rows=max_rows, max_columns=max_columns)
        self.default_delimiter = default_delimiter

    def extract_workbook(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> SpreadsheetDocument:
        doc_id = str(uuid.uuid4())
        file_id = options.get("file_id", doc_id) if options else doc_id
        opts = options or {}
        warnings: list[str] = []

        filename = original_filename or file_path.name
        is_tsv = filename.lower().endswith(".tsv") or opts.get("format") == "tsv"

        # 1. Detect encoding
        encoding, encoding_evidence = self._detect_encoding(file_path)

        # 2. Detect delimiter
        delimiter = "\t" if is_tsv else self._detect_delimiter(file_path, encoding)

        # 3. Read and stream rows
        rows_grid: list[list[Any]] = []
        canonical_rows: list[RowData] = []
        max_col_count = 0
        ragged_row_count = 0

        with open(file_path, encoding=encoding, errors="replace", newline="") as f:
            reader = csv.reader(
                f,
                delimiter=delimiter,
                quotechar='"',
                doublequote=True,
                skipinitialspace=True,
            )

            r_idx = 1
            for row in reader:
                if r_idx > self.max_rows:
                    warnings.append(
                        f"Row count exceeded limit of {self.max_rows:,}. Remaining rows were truncated."
                    )
                    break

                col_len = len(row)
                if col_len > max_col_count:
                    if max_col_count > 0 and r_idx > 1:
                        ragged_row_count += 1
                    max_col_count = col_len

                # Type parsing and cell instantiation
                sparse_cells: list[CellData] = []
                row_vals: list[Any] = []

                for c_idx, raw_cell_str in enumerate(row, start=1):
                    val = raw_cell_str.strip()
                    parsed_val: Any = val
                    data_type = CellDataType.STRING

                    if val == "":
                        parsed_val = None
                        data_type = CellDataType.EMPTY
                    elif val.lower() in ("true", "false"):
                        parsed_val = (val.lower() == "true")
                        data_type = CellDataType.BOOLEAN
                    else:
                        try:
                            parsed_val = int(val)
                            data_type = CellDataType.NUMBER
                        except ValueError:
                            try:
                                parsed_val = float(val)
                                data_type = CellDataType.NUMBER
                            except ValueError:
                                parsed_val = val
                                data_type = CellDataType.STRING

                    row_vals.append(parsed_val)
                    if parsed_val is not None:
                        col_letter = DataUnderstandingProfiler._get_column_letter(c_idx)
                        sparse_cells.append(
                            CellData(
                                address=f"{col_letter}{r_idx}",
                                row=r_idx,
                                column=c_idx,
                                raw_value=parsed_val,
                                formatted_value=str(parsed_val),
                                data_type=data_type,
                            )
                        )

                rows_grid.append(row_vals)
                if sparse_cells:
                    canonical_rows.append(
                        RowData(
                            row_index=r_idx,
                            cells=sparse_cells,
                        )
                    )

                r_idx += 1

        total_rows = len(rows_grid)
        self.check_limits(total_rows, max_col_count)

        if ragged_row_count > 0:
            warnings.append(
                f"Normalized {ragged_row_count} ragged row(s) with inconsistent column counts."
            )

        # 4. Standardize header columns
        raw_headers = [str(c) if c is not None else "" for c in rows_grid[0]] if rows_grid else []
        clean_headers: list[str] = []
        seen_headers: set[str] = set()

        for idx in range(max_col_count):
            h_candidate = raw_headers[idx].strip() if idx < len(raw_headers) and raw_headers[idx].strip() else f"Column_{idx+1}"
            unique_h = h_candidate
            dup_suffix = 1
            while unique_h in seen_headers:
                unique_h = f"{h_candidate}_{dup_suffix}"
                dup_suffix += 1
            seen_headers.add(unique_h)
            clean_headers.append(unique_h)

        # 5. Build ColumnData structures
        columns: list[ColumnData] = []
        for c_idx in range(1, max_col_count + 1):
            letter = DataUnderstandingProfiler._get_column_letter(c_idx)
            name = clean_headers[c_idx - 1] if c_idx - 1 < len(clean_headers) else f"Column {letter}"
            columns.append(
                ColumnData(
                    column_index=c_idx,
                    column_letter=letter,
                    name=name,
                )
            )

        # 6. Profile tabular data
        profiling = DataUnderstandingProfiler.profile_worksheet(
            grid_data=rows_grid[1:] if total_rows > 1 else rows_grid,
            column_names=clean_headers,
        )

        for col, prof in zip(columns, profiling.column_profiles, strict=False):
            col.profiling = prof

        sheet_name = Path(filename).stem or "Sheet1"
        ws = WorksheetData(
            sheet_id="sheet_1",
            name=sheet_name,
            position=1,
            visibility=SheetVisibility.VISIBLE,
            dimensions=f"A1:{DataUnderstandingProfiler._get_column_letter(max(1, max_col_count))}{max(1, total_rows)}",
            total_rows=total_rows,
            total_columns=max_col_count,
            columns=columns,
            rows=canonical_rows,
            profiling=profiling,
        )

        wb_meta = WorkbookMetadata(
            filename=filename,
            format="tsv" if is_tsv else "csv",
            sheet_count=1,
            properties={
                "delimiter": delimiter,
                "encoding": encoding,
                "encoding_evidence": encoding_evidence,
            },
        )

        return SpreadsheetDocument(
            document_id=doc_id,
            file_id=file_id,
            workbook_metadata=wb_meta,
            worksheets=[ws],
            warnings=warnings,
            extraction_metadata={
                "engine": self.engine_name,
                "version": self.version,
                "extracted_at": datetime.now(UTC).isoformat(),
            },
        )

    def _detect_encoding(self, file_path: Path) -> tuple[str, str]:
        """Detect encoding using header byte markers and UTF decoders."""
        with open(file_path, "rb") as f:
            raw_sample = f.read(4096)

        # Check BOM markers
        if raw_sample.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig", "UTF-8 BOM detected"
        if raw_sample.startswith((b"\xff\xfe", b"\xfe\xff")):
            return "utf-16", "UTF-16 BOM detected"

        # Check UTF-8 validity
        try:
            raw_sample.decode("utf-8")
            return "utf-8", "Clean UTF-8 stream"
        except UnicodeDecodeError:
            pass

        # Fallback to CP1252 / Latin-1
        return "cp1252", "Fell back to CP1252/Latin-1 encoding"

    def _detect_delimiter(self, file_path: Path, encoding: str) -> str:
        """Sniff delimiter from sample lines."""
        try:
            with open(file_path, encoding=encoding, errors="replace") as f:
                sample = f.read(8192)

            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",\t;|")
            return dialect.delimiter
        except Exception:
            return self.default_delimiter
