"""JSON output generator for CanonicalDocument."""

import json

from app.domain.schemas.canonical_document import CanonicalDocument


class JSONGenerator:
    """Serializes CanonicalDocument to structured JSON."""

    @classmethod
    def generate(cls, document: CanonicalDocument, indent: int = 2) -> str:
        data = document.model_dump(mode="json")
        return json.dumps(data, indent=indent, ensure_ascii=False)
