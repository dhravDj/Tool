"""Audio document Markdown report generator."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument


class AudioMarkdownGenerator:
    """Generates structured executive Markdown transcription report."""

    @staticmethod
    def _format_time(seconds: float) -> str:
        total_secs = int(round(seconds))
        hrs = total_secs // 3600
        mins = (total_secs % 3600) // 60
        secs = total_secs % 60
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    @classmethod
    def generate(cls, doc: AudioDocument, filename: str = "recording.mp3") -> str:
        """Produce formatted Markdown document with transcript, speakers, and events."""
        duration_fmt = cls._format_time(doc.duration)
        lang_str = (doc.language or "Unknown").capitalize()

        lines: list[str] = [
            "# Audio Transcription",
            "",
            f"**File:** `{filename}`  ",
            f"**Format:** {doc.format.upper()} ({doc.codec})  ",
            f"**Duration:** {duration_fmt} ({doc.duration:.1f}s)  ",
            f"**Language:** {lang_str}  ",
            f"**Speakers:** {len(doc.speakers)}  ",
            "",
            "---",
            "",
            "## Transcript",
            "",
        ]

        if not doc.segments:
            lines.append("*No speech segments transcribed.*")
            lines.append("")
        else:
            for seg in doc.segments:
                s_start = cls._format_time(seg.start)
                s_end = cls._format_time(seg.end)
                speaker_tag = f"{seg.speaker_id}: " if seg.speaker_id else ""
                lines.append(f"[{s_start} - {s_end}] **{speaker_tag}**")
                lines.append(f"{seg.text}")
                lines.append("")

        # Sound events section
        if doc.events:
            lines.extend([
                "---",
                "",
                "## Audio Events",
                "",
            ])
            for ev in doc.events:
                ev_start = cls._format_time(ev.start)
                ev_end = cls._format_time(ev.end)
                lines.append(f"- **{ev.category}:** {ev_start}–{ev_end} (conf: {ev.confidence:.2f})")
            lines.append("")

        # Processing info section
        proc_dur = doc.processing_metadata.get("processing_duration_seconds", 0.0)
        lines.extend([
            "---",
            "",
            "## Processing Information",
            "",
            f"- **Model:** `{doc.model_information.model_name}`",
            f"- **Engine:** `{doc.model_information.engine_name}` ({doc.model_information.device})",
            f"- **Processing Duration:** {proc_dur:.2f}s",
            f"- **Confidence:** {doc.confidence * 100:.1f}%",
        ])

        if doc.warnings:
            lines.append("")
            lines.append("### Warnings")
            for w in doc.warnings:
                lines.append(f"- {w}")

        return "\n".join(lines)
