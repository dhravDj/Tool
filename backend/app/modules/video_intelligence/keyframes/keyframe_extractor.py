"""Keyframe selection, thumbnail generation, hash-based deduplication, and asset persistence."""

import hashlib
import logging
from pathlib import Path

import cv2

from app.infrastructure.storage.local import local_storage
from app.modules.video_intelligence.decoding.video_decoder import VideoDecoder
from app.modules.video_intelligence.schemas.video_document import (
    VideoFrame,
    VideoKeyframe,
    VideoScene,
)

logger = logging.getLogger(__name__)


class KeyframeExtractor:
    """Extracts representative scene keyframes, generates thumbnails, and deduplicates assets."""

    def __init__(self, thumbnail_width: int = 320, thumbnail_height: int = 180) -> None:
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height

    async def extract_keyframes_for_scenes(
        self,
        video_path: Path | str,
        file_id: str,
        scenes: list[VideoScene],
        decoder: VideoDecoder,
    ) -> tuple[list[VideoKeyframe], list[VideoFrame]]:
        """Extract representative midpoint keyframe for every scene and store image assets."""
        keyframes: list[VideoKeyframe] = []
        frames: list[VideoFrame] = []
        known_hashes: dict[str, str] = {}  # sha256 -> asset_reference

        for sc in scenes:
            # Pick representative timestamp: midpoint of scene
            mid_ts = round(sc.start + (sc.duration / 2.0), 3)
            # Ensure within scene bounds
            mid_ts = max(sc.start, min(sc.end, mid_ts))

            frame_bgr = decoder.extract_frame_at_timestamp(video_path, mid_ts)
            if frame_bgr is None:
                # Fallback to scene start timestamp
                frame_bgr = decoder.extract_frame_at_timestamp(video_path, sc.start)
            if frame_bgr is None:
                continue

            h, w = frame_bgr.shape[:2]

            # Encode full analysis frame as JPEG
            success, full_buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                continue
            full_bytes = full_buf.tobytes()

            content_hash = hashlib.sha256(full_bytes).hexdigest()
            hash_prefix = content_hash[:12]

            # Asset references
            if content_hash in known_hashes:
                asset_ref = known_hashes[content_hash]
                thumb_ref = asset_ref.replace("keyframe_", "thumb_")
            else:
                asset_ref = f"video_keyframes/{file_id}/keyframe_{sc.scene_id}_{hash_prefix}.jpg"
                thumb_ref = f"video_keyframes/{file_id}/thumb_{sc.scene_id}_{hash_prefix}.jpg"

                # Generate thumbnail
                thumb_bgr = cv2.resize(
                    frame_bgr,
                    (self.thumbnail_width, self.thumbnail_height),
                    interpolation=cv2.INTER_AREA,
                )
                _, thumb_buf = cv2.imencode(".jpg", thumb_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                thumb_bytes = thumb_buf.tobytes()

                # Save to local_storage
                try:
                    await local_storage.save_file(asset_ref, full_bytes, folder="assets")
                    await local_storage.save_file(thumb_ref, thumb_bytes, folder="assets")
                except Exception as e:
                    logger.warning("Could not persist keyframe asset to storage: %s", e)

                known_hashes[content_hash] = asset_ref

            # Create VideoFrame
            frame_id = f"frm_{sc.scene_id}_{hash_prefix[:6]}"
            v_frame = VideoFrame(
                frame_id=frame_id,
                timestamp=mid_ts,
                frame_index=sc.start_frame,
                asset_reference=asset_ref,
                thumbnail_reference=thumb_ref,
                width=w,
                height=h,
                content_hash=content_hash,
            )
            frames.append(v_frame)

            # Create VideoKeyframe
            keyframe_id = f"key_{sc.scene_id}_{hash_prefix[:6]}"
            v_keyframe = VideoKeyframe(
                keyframe_id=keyframe_id,
                scene_id=sc.scene_id,
                frame_id=frame_id,
                timestamp=mid_ts,
                position_type="scene_middle",
                asset_reference=asset_ref,
                thumbnail_reference=thumb_ref,
                summary=f"Representative visual keyframe for {sc.scene_id} at {mid_ts:.2f}s",
            )
            keyframes.append(v_keyframe)

            # Link back to scene
            sc.representative_keyframe_id = keyframe_id
            if frame_id not in sc.frame_references:
                sc.frame_references.append(frame_id)

        return keyframes, frames
