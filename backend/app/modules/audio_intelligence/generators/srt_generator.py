"""SubRip Subtitle (SRT) format generator."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument


class AudioSRTGenerator:
    """Generates standard RFC/spec SubRip (.srt) subtitle files."""

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        total_ms = max(0, int(round(seconds * 1000)))
        hrs = total_ms // 3600000
        mins = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

    @classmethod
    def generate(cls, doc: AudioDocument, include_speakers: bool = False) -> str:
        """Produce valid SRT file content."""
        blocks: list[str] = []

        for idx, seg in enumerate(doc.segments, start=1):
            t_start = cls._format_srt_timestamp(seg.start)
            t_end = cls._format_srt_timestamp(seg.end)

            text = seg.text.strip()
            if include_speakers and seg.speaker_id:
                text = f"[{seg.speaker_id}] {text}"

            block = f"{idx}\n{t_start} --> {t_end}\n{text}"
            blocks.append(block)

        return "\n\n".join(blocks) + "\n" if blocks else ""
