"""Audio document plain text generator."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument


class AudioTextGenerator:
    """Generates plain text transcript with optional speaker tags."""

    @staticmethod
    def generate(doc: AudioDocument, include_speakers: bool = True) -> str:
        """Produce clean text transcript."""
        if not doc.segments:
            return doc.transcript or ""

        lines: list[str] = []
        for seg in doc.segments:
            if include_speakers and seg.speaker_id:
                lines.append(f"{seg.speaker_id}: {seg.text}")
            else:
                lines.append(seg.text)

        return "\n\n".join(lines)
