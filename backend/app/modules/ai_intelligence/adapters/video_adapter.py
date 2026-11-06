"""Video Content Adapter (Phase 8: MP4, AVI, MKV, MOV, WEBM, FLV, WMV, M4V)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


def _fmt_ts(seconds: float | None) -> str:
    if seconds is None:
        return "00:00:00"
    total_sec = max(0.0, float(seconds))
    hrs = int(total_sec // 3600)
    mins = int((total_sec % 3600) // 60)
    secs = int(total_sec % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


class VideoContentAdapter(BaseContentAdapter):
    """Adapts Phase 8 VideoDocument into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        vid_dict = data.model_dump() if isinstance(data, BaseModel) else data
        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        seen_citations: set[str] = set()
        full_text_parts: list[str] = []

        # 1. Transcript segments (if speech detected/transcribed)
        transcript_segs = vid_dict.get("transcript_segments", [])
        for idx, seg in enumerate(transcript_segs):
            text = (seg.get("text") or "").strip()
            if not text:
                continue

            speaker = seg.get("speaker")
            start = float(seg.get("start_time", 0.0) or 0.0)
            end = float(seg.get("end_time", start) or start)
            start_str = _fmt_ts(start)
            end_str = _fmt_ts(end)

            citation = f"{filename} — {start_str}–{end_str}"
            speaker_prefix = f"[{speaker}] " if speaker else ""
            seg_text = f"{speaker_prefix}{text}"
            full_text_parts.append(seg_text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="video",
                formatted_citation=citation,
                timestamp_start=start,
                timestamp_end=end,
                metadata={"speaker": speaker},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"vid_{file_id[:8]}_ts_{idx}",
                    content=seg_text,
                    block_type="transcript",
                    source_reference=src_ref,
                    token_estimate=max(1, len(seg_text.split())),
                    extraction_confidence=seg.get("confidence"),
                    metadata={"start_time": start, "end_time": end, "speaker": speaker},
                )
            )

        # 2. Scene summaries
        scenes = vid_dict.get("scenes", [])
        for idx, scn in enumerate(scenes):
            scene_idx = scn.get("scene_index", idx + 1)
            start = float(scn.get("start_time", 0.0) or 0.0)
            end = float(scn.get("end_time", start) or start)
            start_str = _fmt_ts(start)
            end_str = _fmt_ts(end)

            desc = scn.get("description") or scn.get("summary") or ""
            ocr_texts = scn.get("ocr_texts") or []
            if ocr_texts and isinstance(ocr_texts, list):
                desc += " | On-screen text: " + "; ".join(ocr_texts)

            if not desc.strip():
                desc = f"Scene {scene_idx} ({start_str} to {end_str})"

            citation = f"{filename} — Scene {scene_idx} ({start_str}–{end_str})"
            full_text_parts.append(f"Scene {scene_idx}: {desc}")

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="video",
                formatted_citation=citation,
                timestamp_start=start,
                timestamp_end=end,
                scene_id=str(scene_idx),
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"vid_{file_id[:8]}_scn_{scene_idx}",
                    content=desc,
                    block_type="scene",
                    source_reference=src_ref,
                    token_estimate=max(1, len(desc.split())),
                    metadata={"scene_index": scene_idx, "start_time": start, "end_time": end},
                )
            )

        # 3. Keyframe OCR results / visual events
        keyframes = vid_dict.get("keyframes", [])
        for idx, kf in enumerate(keyframes):
            ocr_text = (kf.get("ocr_text") or "").strip()
            labels = kf.get("labels") or []
            if not ocr_text and not labels:
                continue

            ts = float(kf.get("timestamp", 0.0) or 0.0)
            ts_str = _fmt_ts(ts)
            content_desc = []
            if ocr_text:
                content_desc.append(f"On-screen text: {ocr_text}")
            if labels:
                content_desc.append(f"Visual objects: {', '.join(labels)}")
            block_content = " | ".join(content_desc)

            citation = f"{filename} — Keyframe at {ts_str}"
            full_text_parts.append(block_content)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="video",
                formatted_citation=citation,
                timestamp_start=ts,
                timestamp_end=ts,
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"vid_{file_id[:8]}_kf_{idx}",
                    content=block_content,
                    block_type="caption",
                    source_reference=src_ref,
                    token_estimate=max(1, len(block_content.split())),
                    metadata={"timestamp": ts},
                )
            )

        # Fallback if no segments/scenes
        if not content_blocks:
            meta = vid_dict.get("metadata", {})
            dur = float(vid_dict.get("duration", 0.0) or 0.0)
            summary_desc = (
                f"Video {filename} (Duration: {_fmt_ts(dur)}, "
                f"Resolution: {meta.get('width', 0)}x{meta.get('height', 0)}, "
                f"Codec: {meta.get('video_codec', 'unknown')})"
            )
            full_text_parts.append(summary_desc)
            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="video",
                formatted_citation=f"{filename} — Video Overview",
                timestamp_start=0.0,
                timestamp_end=dur,
            )
            source_refs.append(src_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"vid_{file_id[:8]}_overview",
                    content=summary_desc,
                    block_type="metadata",
                    source_reference=src_ref,
                    token_estimate=max(1, len(summary_desc.split())),
                )
            )

        combined_text = "\n".join(full_text_parts)
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_vid_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="video",
            content_type=vid_dict.get("format", "video"),
            title=filename,
            content_blocks=content_blocks,
            metadata={
                "duration": vid_dict.get("duration"),
                "scene_count": len(scenes),
                "keyframe_count": len(keyframes),
                "format": vid_dict.get("format"),
            },
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
