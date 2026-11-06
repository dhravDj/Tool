"""Execution manifest and keyframe manifest generators."""

import json

from app.modules.video_intelligence.schemas.video_document import (
    VideoDocument,
    VideoKeyframe,
    VideoManifest,
)


class VideoManifestGenerator:
    """Generates execution audit manifest recording processing artifacts, parameters, and timings."""

    def generate(self, manifest: VideoManifest) -> str:
        """Serialize VideoManifest to JSON."""
        return json.dumps(manifest.model_dump(mode="json"), indent=2)


class VideoKeyframesManifestGenerator:
    """Generates keyframes catalog manifest linking scene IDs, timestamps, and storage asset paths."""

    def generate(self, doc: VideoDocument, keyframes: list[VideoKeyframe]) -> str:
        """Produce structured JSON catalog of keyframe assets."""
        data = {
            "document_id": doc.document_id,
            "file_id": doc.source_file_id,
            "filename": doc.metadata.filename,
            "total_keyframes": len(keyframes),
            "keyframes": [
                {
                    "keyframe_id": kf.keyframe_id,
                    "scene_id": kf.scene_id,
                    "timestamp": kf.timestamp,
                    "position_type": kf.position_type,
                    "asset_reference": kf.asset_reference,
                    "thumbnail_reference": kf.thumbnail_reference,
                    "summary": kf.summary,
                }
                for kf in keyframes
            ],
        }
        return json.dumps(data, indent=2)
