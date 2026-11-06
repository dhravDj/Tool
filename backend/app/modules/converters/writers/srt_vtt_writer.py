"""SRT and WebVTT subtitle writers for audio and video transcripts."""

from app.modules.converters.schemas import UniversalContent, UniversalTranscriptSegment


class SubtitleWriter:
    """Generates standard SRT and WebVTT subtitle tracks."""

    @classmethod
    def write_srt(cls, content: UniversalContent) -> str:
        """Format transcript segments into SubRip (.srt) subtitle text."""
        segments = content.transcript_segments
        if not segments:
            # If no timed segments exist, create a single 0-5s subtitle with raw text or paragraphs
            text = content.raw_text.strip() or " ".join(content.paragraphs).strip()
            if not text:
                return ""
            segments = [UniversalTranscriptSegment(start_seconds=0.0, end_seconds=5.0, text=text)]

        lines: list[str] = []
        for idx, seg in enumerate(segments, start=1):
            start_str = cls._format_timestamp_srt(seg.start_seconds)
            end_str = cls._format_timestamp_srt(seg.end_seconds)
            speaker_str = f"[{seg.speaker}] " if seg.speaker else ""
            lines.append(str(idx))
            lines.append(f"{start_str} --> {end_str}")
            lines.append(f"{speaker_str}{seg.text.strip()}")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    @classmethod
    def write_vtt(cls, content: UniversalContent) -> str:
        """Format transcript segments into WebVTT (.vtt) subtitle text."""
        segments = content.transcript_segments
        if not segments:
            text = content.raw_text.strip() or " ".join(content.paragraphs).strip()
            if not text:
                return "WEBVTT\n"
            segments = [UniversalTranscriptSegment(start_seconds=0.0, end_seconds=5.0, text=text)]

        lines: list[str] = ["WEBVTT", ""]
        if content.title:
            lines.append(f"NOTE Title: {content.title}")
            lines.append("")

        for idx, seg in enumerate(segments, start=1):
            start_str = cls._format_timestamp_vtt(seg.start_seconds)
            end_str = cls._format_timestamp_vtt(seg.end_seconds)
            speaker_str = f"<v {seg.speaker}>" if seg.speaker else ""
            speaker_close = "</v>" if seg.speaker else ""
            lines.append(str(idx))
            lines.append(f"{start_str} --> {end_str}")
            lines.append(f"{speaker_str}{seg.text.strip()}{speaker_close}")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """Format seconds as 00:00:00,000."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_timestamp_vtt(seconds: float) -> str:
        """Format seconds as 00:00:00.000."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"
