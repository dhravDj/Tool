"""Multimodal temporal timeline synchronization connecting audio, video, OCR, and object tracks."""

import logging

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioEvent,
    AudioSegment,
    Speaker,
)
from app.modules.video_intelligence.schemas.video_document import (
    TimelineEvent,
    VideoEvent,
    VideoFrame,
    VideoKeyframe,
    VideoScene,
    VideoTrack,
)

logger = logging.getLogger(__name__)


class MultimodalTimelineBuilder:
    """Synchronizes multimodal signals into a unified chronological master timeline."""

    def build_timeline(
        self,
        scenes: list[VideoScene],
        keyframes: list[VideoKeyframe],
        frames: list[VideoFrame],
        tracks: list[VideoTrack],
        visual_events: list[VideoEvent],
        transcript_segments: list[AudioSegment],
        speakers: list[Speaker],
        audio_events: list[AudioEvent],
        audio_offset_seconds: float = 0.0,
    ) -> list[TimelineEvent]:
        """Construct unified chronological timeline."""
        timeline: list[TimelineEvent] = []

        # 1. Scenes
        for sc in scenes:
            timeline.append(
                TimelineEvent(
                    event_type="scene",
                    start=sc.start,
                    end=sc.end,
                    label=f"Scene {sc.scene_id}",
                    summary=f"Scene duration {sc.duration:.2f}s ({sc.transition_type} transition)",
                    source_reference=sc.scene_id,
                    related_entities=[sc.representative_keyframe_id] if sc.representative_keyframe_id else [],
                )
            )

        # 2. Keyframes
        for kf in keyframes:
            timeline.append(
                TimelineEvent(
                    event_type="keyframe",
                    start=kf.timestamp,
                    end=round(kf.timestamp + 0.1, 3),
                    label="Keyframe",
                    summary=kf.summary,
                    source_reference=kf.keyframe_id,
                    related_entities=[kf.scene_id, kf.frame_id],
                )
            )

        # 3. OCR Text Detections
        for f in frames:
            for ocr in f.ocr_results:
                timeline.append(
                    TimelineEvent(
                        event_type="ocr",
                        start=f.timestamp,
                        end=round(f.timestamp + 0.5, 3),
                        label="On-Screen Text",
                        summary=f'Text detected: "{ocr.text[:60]}"',
                        source_reference=ocr.ocr_id,
                        related_entities=[f.frame_id],
                    )
                )

        # 4. Object Tracks
        for tr in tracks:
            timeline.append(
                TimelineEvent(
                    event_type="object_track",
                    start=tr.first_seen_seconds,
                    end=tr.last_seen_seconds,
                    label=f"Tracked {tr.object_class.title()}",
                    summary=f"{tr.object_class.title()} {tr.track_id} observed across {len(tr.observations)} frames",
                    source_reference=tr.track_id,
                    related_entities=[obs.frame_id for obs in tr.observations],
                )
            )

        # 5. Visual Events
        for vev in visual_events:
            timeline.append(
                TimelineEvent(
                    event_type="visual_event",
                    start=vev.start,
                    end=vev.end,
                    label=vev.category.replace("_", " ").title(),
                    summary=vev.description,
                    source_reference=vev.event_id,
                    related_entities=(vev.related_track_ids + vev.related_frame_ids),
                )
            )

        # 6. Audio Transcript Segments (synchronized with video timeline offset)
        for seg in transcript_segments:
            sync_start = round(seg.start + audio_offset_seconds, 3)
            sync_end = round(seg.end + audio_offset_seconds, 3)
            spk_label = seg.speaker_id or "Speaker"
            timeline.append(
                TimelineEvent(
                    event_type="speech",
                    start=sync_start,
                    end=sync_end,
                    label=f"Speech ({spk_label})",
                    summary=f'{spk_label}: "{seg.text}"',
                    source_reference=seg.segment_id,
                    related_entities=[seg.speaker_id] if seg.speaker_id else [],
                )
            )

        # 7. Audio Events (Music, Silence, Applause, Noise)
        for aev in audio_events:
            sync_start = round(aev.start + audio_offset_seconds, 3)
            sync_end = round(aev.end + audio_offset_seconds, 3)
            timeline.append(
                TimelineEvent(
                    event_type="audio_event",
                    start=sync_start,
                    end=sync_end,
                    label=f"Sound: {aev.category.title()}",
                    summary=f"Detected {aev.category} event ({sync_end - sync_start:.2f}s)",
                    source_reference=aev.event_id,
                    related_entities=[],
                )
            )

        # Sort chronologically by start timestamp, then end timestamp
        timeline.sort(key=lambda item: (item.start, item.end))
        return timeline
