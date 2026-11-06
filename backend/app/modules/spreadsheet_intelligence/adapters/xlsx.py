"""Modern Excel XLSX Spreadsheet Adapter using openpyxl.

Extracts multi-sheet workbooks, formula expressions, cached values,
formatting, merged ranges, tables, charts, data validation, and profiles data.
"""

import logging
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet as OpenPyXLWorksheet

from app.modules.spreadsheet_intelligence.adapters.base import (
    BaseSpreadsheetAdapter,
    SpreadsheetLimitsExceededError,
)
from app.modules.spreadsheet_intelligence.profiling.profiler import DataUnderstandingProfiler
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    CellData,
    CellDataType,
    CellStyle,
    ChartMetadata,
    ColumnData,
    ConditionalFormatRule,
    DataValidationMetadata,
    DefinedName,
    RowData,
    SheetVisibility,
    SpreadsheetDocument,
    TableMetadata,
    WorkbookMetadata,
    WorksheetData,
)

logger = logging.getLogger(__name__)


class XLSXAdapter(BaseSpreadsheetAdapter):
    """High-fidelity extraction engine for Microsoft Excel .xlsx workbooks."""

    format_id = "xlsx"
    engine_name = "openpyxl_adapter"
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
            # 1. Load workbook in structure/formula mode (data_only=False)
            wb_formula = openpyxl.load_workbook(
                str(file_path),
                data_only=False,
                keep_vba=False,
            )

            # 2. Load workbook in evaluation mode (data_only=True) to extract cached values
            wb_cached = None
            try:
                wb_cached = openpyxl.load_workbook(
                    str(file_path),
                    data_only=True,
                    keep_vba=False,
                    read_only=True,
                )
            except Exception as e:
                warnings.append(f"Cached values could not be read separately ({e}); formulas will be extracted without cached results.")

            # Workbook Metadata
            props = wb_formula.properties
            wb_meta = WorkbookMetadata(
                filename=original_filename or file_path.name,
                format="xlsx",
                creator=getattr(props, "creator", None),
                last_modified_by=getattr(props, "lastModifiedBy", None),
                created_at=props.created.isoformat() if getattr(props, "created", None) else None,
                modified_at=props.modified.isoformat() if getattr(props, "modified", None) else None,
                sheet_count=len(wb_formula.sheetnames),
                calculation_settings={"mode": getattr(wb_formula.calculation, "calcMode", "auto") if hasattr(wb_formula, "calculation") else "auto"},
                properties={"title": getattr(props, "title", None), "subject": getattr(props, "subject", None)},
            )

            # Defined Names / Named Ranges
            defined_names: list[DefinedName] = []
            try:
                for name, item in wb_formula.defined_names.items():
                    defined_names.append(
                        DefinedName(
                            name=str(name),
                            value=str(getattr(item, "attr_text", "") or getattr(item, "value", "")),
                            scope="workbook",
                        )
                    )
            except Exception:
                pass

            # Worksheets
            worksheets: list[WorksheetData] = []
            for sheet_idx, sheet_name in enumerate(wb_formula.sheetnames):
                ws: OpenPyXLWorksheet = wb_formula[sheet_name]
                ws_cached = wb_cached[sheet_name] if wb_cached and sheet_name in wb_cached.sheetnames else None

                # Visibility
                vis_state = getattr(ws, "sheet_state", "visible")
                if vis_state == "hidden":
                    visibility = SheetVisibility.HIDDEN
                elif vis_state == "veryHidden":
                    visibility = SheetVisibility.VERY_HIDDEN
                else:
                    visibility = SheetVisibility.VISIBLE

                max_r = ws.max_row or 0
                max_c = ws.max_column or 0
                self.check_limits(max_r, max_c)

                # Merged Ranges
                merged_ranges = [str(r) for r in ws.merged_cells.ranges]

                # Tables
                tables: list[TableMetadata] = []
                try:
                    for tbl in ws.tables.values():
                        tbl_cols = [c.name for c in getattr(tbl, "tableColumns", [])]
                        tables.append(
                            TableMetadata(
                                name=tbl.name,
                                display_name=tbl.displayName or tbl.name,
                                reference_range=tbl.ref,
                                columns=tbl_cols,
                                has_totals_row=bool(getattr(tbl, "totalsRowCount", 0)),
                            )
                        )
                except Exception:
                    pass

                # Charts
                charts: list[ChartMetadata] = []
                try:
                    for ch in getattr(ws, "_charts", []):
                        ch_title = None
                        if hasattr(ch, "title") and ch.title:
                            ch_title = str(getattr(ch.title, "text", ch.title))
                        charts.append(
                            ChartMetadata(
                                title=ch_title,
                                chart_type=ch.__class__.__name__.lower().replace("chart", ""),
                                series_count=len(getattr(ch, "series", [])),
                            )
                        )
                except Exception:
                    pass

                # Data Validation
                validations: list[DataValidationMetadata] = []
                try:
                    for dv in getattr(ws.data_validations, "dataValidation", []):
                        validations.append(
                            DataValidationMetadata(
                                validation_type=dv.type or "custom",
                                formula1=str(dv.formula1) if dv.formula1 else None,
                                formula2=str(dv.formula2) if dv.formula2 else None,
                                ranges=[str(sqref) for sqref in dv.sqref.ranges] if hasattr(dv, "sqref") and dv.sqref else [],
                            )
                        )
                except Exception:
                    pass

                # Conditional Formats
                conditional_formats: list[ConditionalFormatRule] = []
                try:
                    for cf in ws.conditional_formatting:
                        for rule in cf.rules:
                            conditional_formats.append(
                                ConditionalFormatRule(
                                    rule_type=rule.type or "cellIs",
                                    priority=rule.priority or 0,
                                    ranges=[str(r) for r in cf.cells.ranges],
                                    formula=str(rule.formula[0]) if getattr(rule, "formula", None) else None,
                                )
                            )
                except Exception:
                    pass

                # Cells extraction and grid building for profiling
                grid_rows: list[list[Any]] = []
                canonical_rows: list[RowData] = []

                # Column headers map
                col_headers: list[str] = []

                # Process rows
                for r_idx, row in enumerate(ws.iter_rows(values_only=False), start=1):
                    row_vals: list[Any] = []
                    sparse_cells: list[CellData] = []

                    for c_idx, cell in enumerate(row, start=1):
                        val = cell.value
                        is_formula = False
                        formula_str = None
                        cached_val = None

                        if str(val).startswith("="):
                            is_formula = True
                            formula_str = str(val)
                            # Lookup cached value from ws_cached
                            if ws_cached:
                                try:
                                    cached_val = ws_cached.cell(row=r_idx, column=c_idx).value
                                except Exception:
                                    pass

                        # Determine cell data type
                        if is_formula:
                            data_type = CellDataType.FORMULA
                        elif isinstance(val, (int, float)) and not isinstance(val, bool):
                            data_type = CellDataType.NUMBER
                        elif isinstance(val, bool):
                            data_type = CellDataType.BOOLEAN
                        elif isinstance(val, (datetime, date)):
                            data_type = CellDataType.DATETIME
                        elif val is None or str(val).strip() == "":
                            data_type = CellDataType.EMPTY
                        else:
                            data_type = CellDataType.STRING

                        # Formatted display value
                        fmt_val = str(cached_val if is_formula and cached_val is not None else val) if val is not None else ""

                        # Extract styling if not default
                        style = None
                        if cell.has_style:
                            style = CellStyle(
                                font_name=cell.font.name if cell.font else None,
                                font_size=float(cell.font.size) if cell.font and cell.font.size else None,
                                bold=bool(cell.font.bold) if cell.font else False,
                                italic=bool(cell.font.italic) if cell.font else False,
                                font_color=str(cell.font.color.rgb) if cell.font and cell.font.color and hasattr(cell.font.color, "rgb") else None,
                                horizontal_align=cell.alignment.horizontal if cell.alignment else None,
                                vertical_align=cell.alignment.vertical if cell.alignment else None,
                                number_format=cell.number_format if cell.number_format and cell.number_format != "General" else None,
                                has_border=bool(cell.border and (cell.border.left.style or cell.border.top.style or cell.border.right.style or cell.border.bottom.style)),
                            )

                        # Hyperlink & Comments
                        hlink = cell.hyperlink.target if cell.hyperlink else None
                        comment_text = cell.comment.text if cell.comment else None

                        # Only append non-empty cells to sparse representation
                        effective_val = cached_val if is_formula and cached_val is not None else val
                        row_vals.append(effective_val)

                        if val is not None or is_formula or comment_text or hlink:
                            sparse_cells.append(
                                CellData(
                                    address=cell.coordinate,
                                    row=r_idx,
                                    column=c_idx,
                                    raw_value=val,
                                    formatted_value=fmt_val,
                                    data_type=data_type,
                                    formula=formula_str,
                                    cached_value=cached_val,
                                    style=style,
                                    hyperlink=hlink,
                                    comment=comment_text,
                                )
                            )

                    # Header inference from row 1
                    if r_idx == 1:
                        col_headers = [str(v or f"Col_{i+1}") for i, v in enumerate(row_vals)]

                    grid_rows.append(row_vals)

                    if sparse_cells:
                        canonical_rows.append(
                            RowData(
                                row_index=r_idx,
                                height=float(ws.row_dimensions[r_idx].height) if r_idx in ws.row_dimensions and ws.row_dimensions[r_idx].height else None,
                                is_hidden=bool(ws.row_dimensions[r_idx].hidden) if r_idx in ws.row_dimensions else False,
                                cells=sparse_cells,
                            )
                        )

                # Column metadata
                columns: list[ColumnData] = []
                for c_idx in range(1, max_c + 1):
                    letter = openpyxl.utils.get_column_letter(c_idx)
                    col_dim = ws.column_dimensions.get(letter)
                    col_name = col_headers[c_idx - 1] if c_idx - 1 < len(col_headers) else f"Column {letter}"
                    columns.append(
                        ColumnData(
                            column_index=c_idx,
                            column_letter=letter,
                            name=col_name,
                            width=float(col_dim.width) if col_dim and col_dim.width else None,
                            is_hidden=bool(col_dim.hidden) if col_dim else False,
                        )
                    )

                # Profile sheet
                profiling = DataUnderstandingProfiler.profile_worksheet(
                    grid_data=grid_rows,
                    column_names=col_headers,
                )

                # Attach profiling back to columns
                for col, prof in zip(columns, profiling.column_profiles, strict=False):
                    col.profiling = prof

                worksheets.append(
                    WorksheetData(
                        sheet_id=f"sheet_{sheet_idx + 1}",
                        name=sheet_name,
                        position=sheet_idx + 1,
                        visibility=visibility,
                        dimensions=ws.dimensions or f"A1:{openpyxl.utils.get_column_letter(max(1, max_c))}{max(1, max_r)}",
                        total_rows=max_r,
                        total_columns=max_c,
                        merged_ranges=merged_ranges,
                        columns=columns,
                        rows=canonical_rows,
                        tables=tables,
                        charts=charts,
                        validations=validations,
                        conditional_formats=conditional_formats,
                        profiling=profiling,
                    )
                )

            # Close openpyxl workbooks
            wb_formula.close()
            if wb_cached:
                wb_cached.close()

            return SpreadsheetDocument(
                document_id=doc_id,
                file_id=file_id,
                workbook_metadata=wb_meta,
                worksheets=worksheets,
                defined_names=defined_names,
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
            logger.error(f"Failed to extract XLSX workbook '{file_path}': {exc}")
            raise
