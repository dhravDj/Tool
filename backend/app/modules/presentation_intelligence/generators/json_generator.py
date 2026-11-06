"""JSON generator for Presentation Intelligence canonical documents."""

from typing import Any

from app.modules.presentation_intelligence.schemas.presentation_document import (
    PresentationDocument,
)


class PresentationJSONGenerator:
    """Generates canonical indented JSON from a PresentationDocument."""

    @classmethod
    def generate(cls, doc: PresentationDocument) -> str:
        """Serialize PresentationDocument into canonical formatted JSON."""
        return doc.model_dump_json(indent=2)

    @classmethod
    def generate_dict(cls, doc: PresentationDocument) -> dict[str, Any]:
        """Serialize PresentationDocument into a standard Python dictionary."""
        return doc.model_dump()
