"""CSV exporter for canonical worksheets with formula injection sanitization."""

import csv
import io

from app.modules.spreadsheet_intelligence.formulas.inspector import FormulaInspector
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    WorksheetData,
)


class SpreadsheetCSVExporter:
    """Exports a worksheet to CSV format with optional DDE formula sanitization."""

    @staticmethod
    def export_sheet_csv(
        worksheet: WorksheetData,
        sanitize_formulas: bool = True,
    ) -> str:
        """Render worksheet rows into a RFC 4180 CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        # Reconstruct grid from sparse row representation
        for row in worksheet.rows:
            if not row.cells:
                writer.writerow([])
                continue

            max_col = max(c.column for c in row.cells)
            row_data = [""] * max_col

            for cell in row.cells:
                raw = cell.formatted_value if cell.formatted_value is not None else cell.raw_value
                if sanitize_formulas:
                    row_data[cell.column - 1] = FormulaInspector.sanitize_for_csv_export(raw)
                else:
                    row_data[cell.column - 1] = str(raw) if raw is not None else ""

            writer.writerow(row_data)

        return output.getvalue()
