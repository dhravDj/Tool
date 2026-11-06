"""Audio Content Adapter (Phase 7: MP3, WAV, M4A, AAC, FLAC, OGG)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


def format_seconds(seconds: float) -> str:
    """Format float seconds to MM:SS string."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


class AudioContentAdapter(BaseContentAdapter):
    """Adapts Phase 7 AudioDocument structures into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        audio_doc = data.model_dump() if isinstance(data, BaseModel) else data
        transcription = audio_doc.get("transcription") or {}
        segments = (
            transcription.get("segments")
            or audio_doc.get("transcript_segments")
            or audio_doc.get("segments")
            or []
        )

        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        full_text_parts: list[str] = []

        # 1. Timed Transcription Segments
        if segments:
            # Group into ~30 second conversational chunks
            chunk_buf: list[dict[str, Any]] = []
            chunk_start = 0.0

            for idx, seg in enumerate(segments):
                chunk_buf.append(seg)
                seg_end = float(seg.get("end", seg.get("end_time", 0.0)) or 0.0)

                # Split after 5 segments or 30 seconds
                if len(chunk_buf) >= 5 or idx == len(segments) - 1:
                    t_start = float(chunk_buf[0].get("start", chunk_buf[0].get("start_time", chunk_start)) or 0.0)
                    t_end = seg_end
                    time_label = f"{format_seconds(t_start)}–{format_seconds(t_end)}"
                    citation_str = f"{filename} — {time_label}"

                    seg_texts = []
                    for s in chunk_buf:
                        spk = s.get("speaker") or "Speaker"
                        stxt = s.get("text", "").strip()
                        if stxt:
                            seg_texts.append(f"[{spk}] {stxt}")

                    combined_seg_str = "\n".join(seg_texts)
                    full_text_parts.append(combined_seg_str)

                    src_ref = SourceReference(
                        source_file_id=file_id,
                        original_filename=filename,
                        source_type="audio",
                        formatted_citation=citation_str,
                        timestamp_start=t_start,
                        timestamp_end=t_end,
                    )
                    source_refs.append(src_ref)

                    content_blocks.append(
                        ContentBlock(
                            block_id=f"audio_{file_id[:8]}_seg_{idx}",
                            content=combined_seg_str,
                            block_type="transcript_segment",
                            source_reference=src_ref,
                            token_estimate=max(1, len(combined_seg_str.split())),
                            metadata={"timestamp_range": time_label},
                        )
                    )
                    chunk_buf = []
                    chunk_start = seg_end

        # 2. Fallback to Full Transcription text if no granular segments
        if not content_blocks:
            full_txt = transcription.get("full_text") or audio_doc.get("transcription_text") or ""
            if full_txt:
                full_text_parts.append(full_txt)
                src_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="audio",
                    formatted_citation=f"{filename} — Full Audio Transcript",
                    timestamp_start=0.0,
                    timestamp_end=audio_doc.get("duration_seconds", 0.0),
                )
                source_refs.append(src_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"audio_{file_id[:8]}_full",
                        content=full_txt,
                        block_type="transcript_segment",
                        source_reference=src_ref,
                        token_estimate=max(1, len(full_txt.split())),
                    )
                )

        # 3. Sound Events Summary
        events = audio_doc.get("sound_events") or []
        if events:
            event_lines = ["Detected Acoustic Events:"]
            for ev in events:
                e_label = ev.get("label", "event")
                e_time = f"{format_seconds(ev.get('start', 0.0))}–{format_seconds(ev.get('end', 0.0))}"
                event_lines.append(f"• {e_label} ({e_time})")
            ev_text = "\n".join(event_lines)
            full_text_parts.append(ev_text)

            ev_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="audio",
                formatted_citation=f"{filename} — Sound Events",
            )
            source_refs.append(ev_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"audio_{file_id[:8]}_events",
                    content=ev_text,
                    block_type="structured_record",
                    source_reference=ev_ref,
                    token_estimate=max(1, len(ev_text.split())),
                )
            )

        combined_text = "\n\n".join(full_text_parts) or f"Audio file: {filename}"
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_audio_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="audio",
            content_type=audio_doc.get("format", "audio"),
            title=filename,
            content_blocks=content_blocks,
            metadata=audio_doc.get("metadata", {}),
            source_references=source_refs,
            extraction_status="completed",
            language=transcription.get("language", "en"),
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
