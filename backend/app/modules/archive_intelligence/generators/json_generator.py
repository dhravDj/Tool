"""JSON output generator for canonical ArchiveDocument."""

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveJSONGenerator:
    """Serializes canonical ArchiveDocument to standard JSON."""

    def generate(self, doc: ArchiveDocument, indent: int = 2) -> str:
        """Produce formatted JSON representation."""
        return doc.model_dump_json(indent=indent)
