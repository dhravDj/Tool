"""XLSX exporter reconstructing canonical spreadsheet documents back to Excel format."""

import io
from pathlib import Path

import openpyxl

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
)


class SpreadsheetXLSXExporter:
    """Exports canonical SpreadsheetDocument data to a new Excel .xlsx file."""

    @staticmethod
    def export_workbook(doc: SpreadsheetDocument, output_path: Path | None = None) -> bytes:
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        for ws_data in doc.worksheets:
            ws = wb.create_sheet(title=ws_data.name[:31])

            # Populate cells
            for row in ws_data.rows:
                for cell in row.cells:
                    c = ws.cell(row=cell.row, column=cell.column)
                    if cell.formula:
                        c.value = cell.formula
                    else:
                        c.value = cell.raw_value

            # Re-apply merged ranges
            for rng in ws_data.merged_ranges:
                try:
                    ws.merge_cells(rng)
                except Exception:
                    pass

        # Save to buffer
        buf = io.BytesIO()
        wb.save(buf)
        wb.close()
        data = buf.getvalue()

        if output_path:
            output_path.write_bytes(data)

        return data
