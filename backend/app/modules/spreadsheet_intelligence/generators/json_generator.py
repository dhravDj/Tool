"""JSON generator for SpreadsheetDocument."""

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
)


class SpreadsheetJSONGenerator:
    """Serializes canonical SpreadsheetDocument to formatted JSON."""

    @staticmethod
    def generate(doc: SpreadsheetDocument, indent: int = 2) -> str:
        return doc.model_dump_json(indent=indent)
