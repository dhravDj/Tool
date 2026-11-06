"""Audio document JSON serialization generator."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument


class AudioJSONGenerator:
    """Serializes AudioDocument into canonical JSON."""

    @staticmethod
    def generate(doc: AudioDocument, indent: int = 2) -> str:
        """Return formatted JSON string of AudioDocument."""
        return doc.model_dump_json(indent=indent)
