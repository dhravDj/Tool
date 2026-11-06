"""JSON generator for Structured Data Intelligence documents."""

from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)


class StructuredJSONGenerator:
    """Serializes canonical StructuredDataDocument to standardized JSON string."""

    def generate(self, doc: StructuredDataDocument) -> str:
        return doc.model_dump_json(indent=2)
