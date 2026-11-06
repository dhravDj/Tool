"""JSON serialization generator for VideoDocument."""

import json

from app.modules.video_intelligence.schemas.video_document import VideoDocument


class VideoJSONGenerator:
    """Serializes canonical VideoDocument into lossless structured JSON."""

    def generate(self, doc: VideoDocument) -> str:
        """Return formatted JSON string."""
        return json.dumps(doc.model_dump(mode="json"), indent=2, ensure_ascii=False)
