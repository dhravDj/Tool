"""Visual event and activity detector for temporal scene and track changes."""

import logging

from app.modules.video_intelligence.schemas.video_document import (
    VideoEvent,
    VideoFrame,
    VideoScene,
    VideoTrack,
)

logger = logging.getLogger(__name__)


class VisualEventDetector:
    """Analyzes scene cuts, track motion vectors, and frame OCR/visual features to detect visual events."""

    def detect_events(
        self,
        scenes: list[VideoScene],
        tracks: list[VideoTrack],
        frames: list[VideoFrame],
    ) -> list[VideoEvent]:
        """Detect structured visual events across the video timeline."""
        events: list[VideoEvent] = []

        # 1. Scene Transitions
        for sc in scenes:
            if sc.start > 0.0:
                events.append(
                    VideoEvent(
                        category="scene_transition",
                        start=round(sc.start, 3),
                        end=round(min(sc.end, sc.start + 0.4), 3),
                        description=f"Visual {sc.transition_type} transition into {sc.scene_id}",
                        scene_id=sc.scene_id,
                        related_frame_ids=sc.frame_references[:2],
                        confidence=sc.confidence,
                        detection_engine="documind-scene-cut-v1",
                    )
                )

        # 2. Object Track Motion Events (Person/Vehicle entry, traversal, exit)
        for tr in tracks:
            if not tr.observations:
                continue

            first_obs = tr.observations[0]
            last_obs = tr.observations[-1]
            first_box = first_obs.bounding_box
            last_box = last_obs.bounding_box

            # Displacement
            dx = last_box[1] - first_box[1]
            dy = last_box[0] - first_box[0]
            displacement = (dx**2 + dy**2) ** 0.5

            # Find matching scene
            sc_match = next((sc for sc in scenes if sc.start <= tr.first_seen_seconds <= sc.end), None)
            sc_id = sc_match.scene_id if sc_match else None

            if tr.object_class == "person":
                if displacement > 0.15:
                    cat = "person_movement"
                    desc = f"Anonymous person moving across frame ({tr.track_id})"
                else:
                    cat = "general_activity"
                    desc = f"Person detected stationary in frame ({tr.track_id})"

                events.append(
                    VideoEvent(
                        category=cat,
                        start=round(tr.first_seen_seconds, 3),
                        end=round(tr.last_seen_seconds, 3),
                        description=desc,
                        scene_id=sc_id,
                        related_frame_ids=[obs.frame_id for obs in tr.observations],
                        related_track_ids=[tr.track_id],
                        confidence=tr.confidence,
                        detection_engine="documind-motion-v1",
                    )
                )
            elif tr.object_class == "vehicle":
                events.append(
                    VideoEvent(
                        category="vehicle_movement",
                        start=round(tr.first_seen_seconds, 3),
                        end=round(tr.last_seen_seconds, 3),
                        description=f"Vehicle trajectory observed ({tr.track_id})",
                        scene_id=sc_id,
                        related_frame_ids=[obs.frame_id for obs in tr.observations],
                        related_track_ids=[tr.track_id],
                        confidence=tr.confidence,
                        detection_engine="documind-motion-v1",
                    )
                )

        # 3. Presentation / Screen Recording Detection based on OCR and Scene Layout
        for sc in scenes:
            scene_frames = [f for f in frames if f.frame_id in sc.frame_references]
            has_rich_text = any(len(f.ocr_results) >= 2 or len(f.description) > 30 for f in scene_frames)
            if has_rich_text:
                events.append(
                    VideoEvent(
                        category="presentation_slide",
                        start=round(sc.start, 3),
                        end=round(sc.end, 3),
                        description=f"Presentation slide or text document layout displayed in {sc.scene_id}",
                        scene_id=sc.scene_id,
                        related_frame_ids=sc.frame_references,
                        confidence=0.89,
                        detection_engine="documind-layout-v1",
                    )
                )

        # Sort chronologically by start timestamp
        events.sort(key=lambda ev: ev.start)
        return events
