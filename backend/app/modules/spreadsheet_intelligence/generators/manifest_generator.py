"""Operational manifest generator for Spreadsheet Intelligence."""

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
    SpreadsheetManifest,
)


class SpreadsheetManifestGenerator:
    """Generates execution manifest summarizing spreadsheet intelligence processing."""

    @staticmethod
    def generate(
        doc: SpreadsheetDocument,
        status: str,
        engine_name: str,
        engine_version: str,
        duration_seconds: float,
        artifacts: dict[str, str],
        errors: list[str] | None = None,
    ) -> SpreadsheetManifest:
        total_rows = sum(ws.total_rows for ws in doc.worksheets)
        total_cols = sum(ws.total_columns for ws in doc.worksheets)
        total_cells = sum(
            sum(len(r.cells) for r in ws.rows) for ws in doc.worksheets
        )
        total_formulas = sum(
            sum(sum(1 for c in r.cells if c.formula) for r in ws.rows)
            for ws in doc.worksheets
        )

        return SpreadsheetManifest(
            document_id=doc.document_id,
            file_id=doc.file_id,
            source_filename=doc.workbook_metadata.filename,
            source_format=doc.workbook_metadata.format,
            status=status,
            engine_name=engine_name,
            engine_version=engine_version,
            processing_time_seconds=round(duration_seconds, 3),
            worksheet_count=len(doc.worksheets),
            total_rows=total_rows,
            total_columns=total_cols,
            total_cells=total_cells,
            formula_count=total_formulas,
            artifacts=artifacts,
            warnings=doc.warnings,
            errors=errors or [],
        )
