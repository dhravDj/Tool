"""Video adapter converting VideoDocument to UniversalContent."""

from app.modules.converters.schemas import (
    UniversalContent,
    UniversalSection,
    UniversalTable,
    UniversalTranscriptSegment,
)
from app.modules.video_intelligence.schemas.video_document import VideoDocument


class VideoAdapter:
    """Adapts VideoDocument into standard UniversalContent preserving speech transcripts and scene cuts."""

    @classmethod
    def adapt(cls, doc: VideoDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or doc.metadata.filename or f"video.{doc.format}"
        transcript_segments: list[UniversalTranscriptSegment] = []
        paragraphs: list[str] = []
        sections: list[UniversalSection] = []
        tables: list[UniversalTable] = []

        # 1. Audio Transcript Segments
        for seg in doc.transcript_segments:
            seg_text = seg.text.strip()
            if seg_text:
                transcript_segments.append(
                    UniversalTranscriptSegment(
                        start_seconds=seg.start,
                        end_seconds=seg.end,
                        speaker=seg.speaker_id or "",
                        text=seg_text,
                        confidence=seg.confidence,
                    )
                )
                paragraphs.append(seg_text)

        full_transcript = doc.transcript.strip() or "\n".join(paragraphs)
        if full_transcript:
            sections.append(
                UniversalSection(
                    title="Audio Track Transcript",
                    content=full_transcript,
                )
            )

        # 2. Scene Segmentation Table & Report
        if doc.scenes:
            scene_rows: list[list[str]] = []
            scene_bullets: list[str] = []
            for idx, sc in enumerate(doc.scenes, start=1):
                start_m, start_s = divmod(int(sc.start), 60)
                end_m, end_s = divmod(int(sc.end), 60)
                time_range = f"{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}"
                desc = sc.visual_summary or f"Scene transition ({sc.transition_type})"
                scene_rows.append([str(idx), time_range, f"{sc.duration:.1f}s", sc.transition_type, desc])
                scene_bullets.append(f"• Scene {idx} [{time_range}] ({sc.duration:.1f}s): {desc}")

            tables.append(
                UniversalTable(
                    title="Scene Segmentation",
                    headers=["Scene #", "Timestamp", "Duration", "Cut Type", "Visual Content / Activity"],
                    rows=scene_rows,
                    row_count=len(scene_rows),
                    col_count=5,
                )
            )

            sections.append(
                UniversalSection(
                    title="Visual Scene Breakdown",
                    content="\n".join(scene_bullets),
                )
            )

        # 3. Video Metadata
        v_stream = doc.video_streams[0] if doc.video_streams else None
        meta = {
            "duration_seconds": doc.duration,
            "resolution": v_stream.resolution if v_stream else "unknown",
            "fps": v_stream.fps if v_stream else 0.0,
            "video_codec": v_stream.codec if v_stream else "unknown",
            "scene_count": len(doc.scenes),
            "keyframe_count": len(doc.keyframes),
        }

        all_text = (full_transcript + "\n\n" + "\n".join(s.content for s in sections)).strip()

        return UniversalContent(
            source_filename=filename,
            source_format=doc.format,
            title=f"Video: {filename}",
            author="",
            page_count=1,
            word_count=len(all_text.split()),
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            transcript_segments=transcript_segments,
            metadata=meta,
            warnings=doc.warnings,
            raw_text=all_text,
        )
