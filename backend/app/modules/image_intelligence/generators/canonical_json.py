"""Canonical Image Document JSON output generator."""

import json

from app.modules.image_intelligence.schemas.image_document import ImageDocument


class ImageJSONGenerator:
    """Serializes ImageDocument to standardized JSON format."""

    @staticmethod
    def generate(doc: ImageDocument) -> str:
        """Render ImageDocument to pretty-printed JSON string."""
        return json.dumps(doc.model_dump(), indent=2, ensure_ascii=False)
