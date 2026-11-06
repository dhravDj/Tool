"""Legacy Excel XLS (BIFF8 / 97-2003) Spreadsheet Adapter using xlrd."""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import xlrd

from app.modules.spreadsheet_intelligence.adapters.base import (
    BaseSpreadsheetAdapter,
    SpreadsheetLimitsExceededError,
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


class LegacyXLSAdapter(BaseSpreadsheetAdapter):
    """Parses legacy binary Microsoft Excel (.xls) spreadsheets without executing macros."""

    format_id = "xls"
    engine_name = "xlrd_adapter"
    version = "1.0.0"

    def extract_workbook(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> SpreadsheetDocument:
        doc_id = str(uuid.uuid4())
        file_id = options.get("file_id", doc_id) if options else doc_id
        warnings: list[str] = []

        try:
            wb = xlrd.open_workbook(str(file_path), on_demand=False)
            wb_meta = WorkbookMetadata(
                filename=original_filename or file_path.name,
                format="xls",
                creator=getattr(wb, "user_name", None),
                sheet_count=wb.nsheets,
            )

            worksheets: list[WorksheetData] = []
            for sheet_idx in range(wb.nsheets):
                sheet = wb.sheet_by_index(sheet_idx)
                name = sheet.name
                total_r = sheet.nrows
                total_c = sheet.ncols
                self.check_limits(total_r, total_c)

                # Visibility
                vis = getattr(sheet, "visibility", 0)
                if vis == 1:
                    visibility = SheetVisibility.HIDDEN
                elif vis == 2:
                    visibility = SheetVisibility.VERY_HIDDEN
                else:
                    visibility = SheetVisibility.VISIBLE

                # Merged ranges (rlo, rhi, clo, chi)
                merged_ranges: list[str] = []
                for rlo, rhi, clo, chi in getattr(sheet, "merged_cells", []):
                    c1_letter = DataUnderstandingProfiler._get_column_letter(clo + 1)
                    c2_letter = DataUnderstandingProfiler._get_column_letter(chi)
                    merged_ranges.append(f"{c1_letter}{rlo + 1}:{c2_letter}{rhi}")

                grid_rows: list[list[Any]] = []
                canonical_rows: list[RowData] = []
                col_headers: list[str] = []

                for r in range(total_r):
                    row_vals: list[Any] = []
                    sparse_cells: list[CellData] = []

                    for c in range(total_c):
                        cell_type = sheet.cell_type(r, c)
                        val = sheet.cell_value(r, c)

                        data_type = CellDataType.STRING
                        if cell_type == xlrd.XL_CELL_EMPTY:
                            val = None
                            data_type = CellDataType.EMPTY
                        elif cell_type == xlrd.XL_CELL_NUMBER:
                            data_type = CellDataType.NUMBER
                        elif cell_type == xlrd.XL_CELL_DATE:
                            data_type = CellDataType.DATE
                            try:
                                date_tuple = xlrd.xldate_as_tuple(val, wb.datemode)
                                val = f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                            except Exception:
                                pass
                        elif cell_type == xlrd.XL_CELL_BOOLEAN:
                            data_type = CellDataType.BOOLEAN
                            val = bool(val)
                        elif cell_type == xlrd.XL_CELL_ERROR:
                            data_type = CellDataType.ERROR
                            val = f"#ERROR_{val}"

                        row_vals.append(val)
                        if val is not None:
                            col_letter = DataUnderstandingProfiler._get_column_letter(c + 1)
                            sparse_cells.append(
                                CellData(
                                    address=f"{col_letter}{r + 1}",
                                    row=r + 1,
                                    column=c + 1,
                                    raw_value=val,
                                    formatted_value=str(val),
                                    data_type=data_type,
                                )
                            )

                    if r == 0:
                        col_headers = [str(v or f"Col_{i+1}") for i, v in enumerate(row_vals)]

                    grid_rows.append(row_vals)
                    if sparse_cells:
                        canonical_rows.append(
                            RowData(
                                row_index=r + 1,
                                cells=sparse_cells,
                            )
                        )

                # Columns
                columns: list[ColumnData] = []
                for c_idx in range(1, total_c + 1):
                    letter = DataUnderstandingProfiler._get_column_letter(c_idx)
                    c_name = col_headers[c_idx - 1] if c_idx - 1 < len(col_headers) else f"Column {letter}"
                    columns.append(
                        ColumnData(
                            column_index=c_idx,
                            column_letter=letter,
                            name=c_name,
                        )
                    )

                # Profile sheet
                profiling = DataUnderstandingProfiler.profile_worksheet(
                    grid_data=grid_rows,
                    column_names=col_headers,
                )

                for col, prof in zip(columns, profiling.column_profiles, strict=False):
                    col.profiling = prof

                worksheets.append(
                    WorksheetData(
                        sheet_id=f"sheet_{sheet_idx + 1}",
                        name=name,
                        position=sheet_idx + 1,
                        visibility=visibility,
                        dimensions=f"A1:{DataUnderstandingProfiler._get_column_letter(max(1, total_c))}{max(1, total_r)}",
                        total_rows=total_r,
                        total_columns=total_c,
                        merged_ranges=merged_ranges,
                        columns=columns,
                        rows=canonical_rows,
                        profiling=profiling,
                    )
                )

            return SpreadsheetDocument(
                document_id=doc_id,
                file_id=file_id,
                workbook_metadata=wb_meta,
                worksheets=worksheets,
                warnings=warnings,
                extraction_metadata={
                    "engine": self.engine_name,
                    "version": self.version,
                    "extracted_at": datetime.now(UTC).isoformat(),
                },
            )

        except SpreadsheetLimitsExceededError:
            raise
        except Exception as exc:
            logger.error(f"Failed to extract legacy XLS spreadsheet '{file_path}': {exc}")
            raise
