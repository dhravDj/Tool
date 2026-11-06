"""JSON generator for Code Intelligence documents."""

from typing import Any

from app.modules.code_intelligence.schemas.code_document import CodeDocument


class CodeJSONGenerator:
    """Serializes canonical CodeDocument to standardized JSON string."""

    def generate(self, doc: CodeDocument) -> str:
        return doc.model_dump_json(indent=2)

    def generate_dict(self, doc: CodeDocument) -> dict[str, Any]:
        return doc.model_dump()
