"""WebVTT (VTT) subtitle generator."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument


class AudioVTTGenerator:
    """Generates standard W3C WebVTT (.vtt) subtitle files."""

    @staticmethod
    def _format_vtt_timestamp(seconds: float) -> str:
        total_ms = max(0, int(round(seconds * 1000)))
        hrs = total_ms // 3600000
        mins = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"

    @classmethod
    def generate(cls, doc: AudioDocument, include_speakers: bool = False) -> str:
        """Produce valid WebVTT string with WEBVTT header."""
        lines: list[str] = ["WEBVTT", ""]

        for idx, seg in enumerate(doc.segments, start=1):
            t_start = cls._format_vtt_timestamp(seg.start)
            t_end = cls._format_vtt_timestamp(seg.end)

            text = seg.text.strip()
            if include_speakers and seg.speaker_id:
                text = f"<v {seg.speaker_id}>{text}"

            lines.append(str(idx))
            lines.append(f"{t_start} --> {t_end}")
            lines.append(text)
            lines.append("")

        return "\n".join(lines)
