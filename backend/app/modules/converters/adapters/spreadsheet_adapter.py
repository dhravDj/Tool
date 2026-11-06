"""Spreadsheet adapter converting SpreadsheetDocument to UniversalContent."""

from typing import Any

from app.modules.converters.schemas import (
    UniversalContent,
    UniversalSection,
    UniversalTable,
)
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import SpreadsheetDocument


class SpreadsheetAdapter:
    """Adapts SpreadsheetDocument into standard UniversalContent."""

    @classmethod
    def adapt(cls, doc: SpreadsheetDocument) -> UniversalContent:
        tables: list[UniversalTable] = []
        sections: list[UniversalSection] = []
        paragraphs: list[str] = []

        total_cells = 0
        total_rows = 0

        for sheet in doc.worksheets:
            # Build 2D grid
            sheet_rows_dict: dict[int, dict[int, Any]] = {}
            max_col = 0
            max_row = 0

            for r in sheet.rows:
                row_idx = r.row_index
                if row_idx > max_row:
                    max_row = row_idx
                if row_idx not in sheet_rows_dict:
                    sheet_rows_dict[row_idx] = {}

                for c in r.cells:
                    col_idx = c.column
                    if col_idx > max_col:
                        max_col = col_idx
                    # Use formatted_value if available, else raw_value
                    val = c.formatted_value if c.formatted_value is not None else c.raw_value
                    sheet_rows_dict[row_idx][col_idx] = val
                    total_cells += 1

            # Headers from columns or first row
            headers: list[str] = []
            if sheet.columns:
                headers = [col.name or col.column_letter for col in sheet.columns]
                max_col = max(max_col, len(headers))
            elif 1 in sheet_rows_dict:
                first_row = sheet_rows_dict[1]
                headers = [str(first_row.get(i, f"Col {i}")) for i in range(1, max_col + 1)]

            grid_rows: list[list[Any]] = []
            # Start from row 2 if row 1 was used as header, or row 1 if column names were distinct
            start_row = 2 if (not sheet.columns and 1 in sheet_rows_dict) else 1
            for r_num in range(start_row, max_row + 1):
                r_dict = sheet_rows_dict.get(r_num, {})
                row_vals = [r_dict.get(c_num, "") for c_num in range(1, max_col + 1)]
                grid_rows.append(row_vals)

            total_rows += len(grid_rows)

            tbl = UniversalTable(
                title=f"Sheet: {sheet.name}",
                sheet_name=sheet.name,
                headers=headers,
                rows=grid_rows,
                row_count=len(grid_rows),
                col_count=max_col,
            )
            tables.append(tbl)

            # Markdown/Text section summary for this sheet
            sec_summary = (
                f"Worksheet: {sheet.name} | Dimensions: {sheet.dimensions or f'{len(grid_rows)}x{max_col}'}\n"
                f"Columns: {len(headers)} | Populated Rows: {len(grid_rows)}"
            )
            sections.append(
                UniversalSection(
                    title=f"Worksheet: {sheet.name}",
                    content=sec_summary,
                )
            )
            paragraphs.append(sec_summary)

        meta = {
            "creator": doc.workbook_metadata.creator,
            "created_at": doc.workbook_metadata.created_at,
            "sheet_count": len(doc.worksheets),
            "sheet_names": [s.name for s in doc.worksheets],
            "total_rows": total_rows,
            "total_cells": total_cells,
        }

        all_text = "\n\n".join(paragraphs)
        return UniversalContent(
            source_filename=doc.workbook_metadata.filename,
            source_format=doc.workbook_metadata.format,
            title=f"Workbook: {doc.workbook_metadata.filename}",
            author=doc.workbook_metadata.creator or "",
            page_count=len(doc.worksheets),
            word_count=total_cells,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            metadata=meta,
            warnings=doc.warnings,
            raw_text=all_text,
        )
