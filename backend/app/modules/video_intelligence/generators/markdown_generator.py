"""Markdown report generator for VideoDocument preserving scene structure and multimodal timeline."""

from app.modules.video_intelligence.schemas.video_document import VideoDocument


def _format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    s = int(seconds)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class VideoMarkdownGenerator:
    """Generates structured scene-by-scene Markdown reports."""

    def generate(self, doc: VideoDocument) -> str:
        """Produce formatted Markdown documentation for an analyzed video."""
        v_stream = doc.video_streams[0] if doc.video_streams else None
        res_str = v_stream.resolution if v_stream else "Unknown"
        codec_str = v_stream.codec if v_stream else "Unknown"
        fps_str = f"{v_stream.fps:.1f} fps" if v_stream else "N/A"

        lines = [
            "# Video Analysis",
            "",
            f"**Filename:** {doc.metadata.filename or 'video'}",
            f"**Format:** {doc.format.upper()}",
            f"**Duration:** {_format_time(doc.duration)} ({doc.duration:.2f}s)",
            f"**Resolution:** {res_str} ({fps_str}, {codec_str})",
            f"**Scenes Detected:** {len(doc.scenes)}",
            f"**Keyframes:** {len(doc.keyframes)}",
            f"**Visual Objects Tracked:** {len(doc.tracks)}",
            "",
            "---",
            "",
        ]

        # Scene by scene breakdown
        for idx, sc in enumerate(doc.scenes, 1):
            time_range = f"{_format_time(sc.start)} to {_format_time(sc.end)}"
            lines.append(f"## Scene {idx} — {time_range}")
            lines.append("")

            # Visual Summary
            lines.append("### Visual Summary")
            scene_frames = [f for f in doc.frames if f.frame_id in sc.frame_references]
            descriptions = [f.description for f in scene_frames if f.description]
            summary_text = (
                sc.visual_summary
                or (descriptions[0] if descriptions else f"Visual scene with {sc.transition_type} transition.")
            )
            lines.append(summary_text)
            lines.append("")

            # OCR
            lines.append("### OCR")
            ocr_items = []
            for f in scene_frames:
                for ocr in f.ocr_results:
                    ocr_items.append(f"- [{_format_time(f.timestamp)}] {ocr.text}")
            if ocr_items:
                lines.extend(ocr_items)
            else:
                lines.append("_No on-screen text recognized._")
            lines.append("")

            # Objects
            lines.append("### Objects")
            scene_tracks = [
                tr
                for tr in doc.tracks
                if any(sc.start <= obs.timestamp <= sc.end for obs in tr.observations)
            ]
            if scene_tracks:
                for tr in scene_tracks:
                    lines.append(
                        f"- **{tr.object_class.title()}** ({tr.track_id}): {_format_time(tr.first_seen_seconds)}–{_format_time(tr.last_seen_seconds)} (conf: {tr.confidence:.2f})"
                    )
            else:
                lines.append("_No salient object tracks in this scene._")
            lines.append("")

            # Audio Transcript
            lines.append("### Audio Transcript")
            scene_speeches = [
                seg
                for seg in doc.transcript_segments
                if not (seg.end < sc.start or seg.start > sc.end)
            ]
            if scene_speeches:
                for seg in scene_speeches:
                    spk = seg.speaker_id or "Speaker"
                    lines.append(f"- **{spk}** [{_format_time(seg.start)}]: {seg.text}")
            else:
                lines.append("_No speech detected in this scene._")
            lines.append("")

            # Events
            lines.append("### Events")
            scene_events = [
                ev
                for ev in doc.visual_events
                if (ev.scene_id == sc.scene_id or (sc.start <= ev.start <= sc.end))
            ]
            scene_audio_events = [
                aev
                for aev in doc.audio_events
                if (sc.start <= aev.start <= sc.end)
            ]
            if scene_events or scene_audio_events:
                for vev in scene_events:
                    lines.append(f"- Visual: **{vev.category.replace('_', ' ').title()}** — {vev.description}")
                for aev in scene_audio_events:
                    lines.append(f"- Audio: **{aev.category.title()}** [{_format_time(aev.start)}–{_format_time(aev.end)}]")
            else:
                lines.append("_No discrete activity events._")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines).strip()
