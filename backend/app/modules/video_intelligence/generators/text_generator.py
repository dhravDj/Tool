"""Plain text transcript and chronological summary generator for video analysis."""

from app.modules.video_intelligence.schemas.video_document import VideoDocument


def _format_time(seconds: float) -> str:
    s = int(seconds)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class VideoPlainTextGenerator:
    """Exports structured plain-text transcript and event log."""

    def generate(self, doc: VideoDocument) -> str:
        """Produce timestamped plain-text representation."""
        lines = [
            f"VIDEO TRANSCRIPT & TIMELINE — {doc.metadata.filename or 'Video'}",
            f"Duration: {_format_time(doc.duration)} | Format: {doc.format.upper()}",
            "=" * 60,
            "",
        ]

        if doc.timeline:
            for item in doc.timeline:
                start_str = _format_time(item.start)
                end_str = _format_time(item.end)
                lines.append(f"[{start_str} - {end_str}] ({item.event_type.upper()}) {item.label}: {item.summary}")
        elif doc.transcript:
            lines.append(doc.transcript)
        else:
            lines.append("No speech or timeline events detected.")

        return "\n".join(lines)
