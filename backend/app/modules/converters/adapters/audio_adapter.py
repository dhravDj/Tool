"""Audio adapter converting AudioDocument to UniversalContent with timestamps and subtitles."""

from app.modules.audio_intelligence.schemas.audio_document import AudioDocument
from app.modules.converters.schemas import (
    UniversalContent,
    UniversalSection,
    UniversalTranscriptSegment,
)


class AudioAdapter:
    """Adapts AudioDocument into standard UniversalContent preserving speech timestamps and transcripts."""

    @classmethod
    def adapt(cls, doc: AudioDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or f"audio.{doc.format}"
        transcript_segments: list[UniversalTranscriptSegment] = []
        paragraphs: list[str] = []
        warnings: list[str] = list(doc.warnings)

        if doc.model_information.is_heuristic:
            warnings.append(
                "Notice: Speech recognition engine is running in heuristic baseline mode. "
                "For high-accuracy multi-lingual STT (English/Hindi/Hinglish), install faster-whisper or configure whisper.cpp."
            )

        for seg in doc.segments:
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

        sections: list[UniversalSection] = []
        if full_transcript:
            sections.append(
                UniversalSection(
                    title="Audio Speech Transcript",
                    content=full_transcript,
                )
            )

        meta = {
            "duration_seconds": doc.duration,
            "sample_rate": doc.sample_rate,
            "channels": doc.channels,
            "codec": doc.codec,
            "language": doc.language,
            "model_engine": doc.model_information.engine_name,
            "is_heuristic": doc.model_information.is_heuristic,
            "artist": doc.metadata.artist,
            "album": doc.metadata.album,
            "title": doc.metadata.title,
        }

        return UniversalContent(
            source_filename=filename,
            source_format=doc.format,
            title=doc.metadata.title or f"Audio: {filename}",
            author=doc.metadata.artist or "",
            page_count=1,
            word_count=len(full_transcript.split()),
            paragraphs=paragraphs,
            sections=sections,
            transcript_segments=transcript_segments,
            metadata=meta,
            warnings=warnings,
            raw_text=full_transcript,
        )
