"""SubRip (SRT) and WebVTT (VTT) subtitle generators from synchronized video transcripts."""

from app.modules.video_intelligence.schemas.video_document import VideoDocument


def _seconds_to_srt_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS,mmm (comma format)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def _seconds_to_vtt_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm (period format)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


class VideoSubtitleGenerator:
    """Generates standard .srt and .vtt subtitle tracks synchronized with video playback."""

    def generate_srt(self, doc: VideoDocument) -> str:
        """Produce SubRip Subtitle (.srt) format."""
        segments = doc.transcript_segments
        if not segments and doc.scenes:
            # Generate subtitles from scene summaries if no speech audio exists
            entries = []
            for idx, sc in enumerate(doc.scenes, 1):
                start_str = _seconds_to_srt_time(sc.start)
                end_str = _seconds_to_srt_time(sc.end)
                entries.append(f"{idx}\n{start_str} --> {end_str}\n[{sc.scene_id}] {sc.visual_summary or 'Visual scene'}\n")
            return "\n".join(entries).strip()

        entries = []
        for idx, seg in enumerate(segments, 1):
            start_str = _seconds_to_srt_time(seg.start)
            end_str = _seconds_to_srt_time(seg.end)
            spk_prefix = f"[{seg.speaker_id}] " if seg.speaker_id else ""
            entries.append(f"{idx}\n{start_str} --> {end_str}\n{spk_prefix}{seg.text}\n")
        return "\n".join(entries).strip()

    def generate_vtt(self, doc: VideoDocument) -> str:
        """Produce WebVTT Subtitle (.vtt) format."""
        lines = ["WEBVTT", ""]
        segments = doc.transcript_segments
        if not segments and doc.scenes:
            for sc in doc.scenes:
                start_str = _seconds_to_vtt_time(sc.start)
                end_str = _seconds_to_vtt_time(sc.end)
                lines.append(f"{start_str} --> {end_str}")
                lines.append(f"[{sc.scene_id}] {sc.visual_summary or 'Visual scene'}\n")
            return "\n".join(lines).strip()

        for seg in segments:
            start_str = _seconds_to_vtt_time(seg.start)
            end_str = _seconds_to_vtt_time(seg.end)
            spk_prefix = f"<v {seg.speaker_id}>" if seg.speaker_id else ""
            lines.append(f"{start_str} --> {end_str}")
            lines.append(f"{spk_prefix}{seg.text}\n")
        return "\n".join(lines).strip()
