# DocuMind AI — Video Document Canonical Schema

## 1. Schema Hierarchy

The canonical schema for Phase 8 is `VideoDocument`, representing the full multimodal extraction and intelligence state of a video recording.

```json
{
  "document_id": "vid_6346490f-1a66-4b52-823e-5ef274ae25ad",
  "file_id": "file_uuid_1234",
  "filename": "presentation.mp4",
  "format": "mp4",
  "duration": 120.5,
  "video_metadata": {
    "filename": "presentation.mp4",
    "container_format": "mov,mp4,m4a,3gp,3g2,mj2",
    "file_size_bytes": 10485760,
    "duration_seconds": 120.5,
    "bitrate_kbps": 696.2,
    "stream_count": 2,
    "tags": {},
    "video_streams": [
      {
        "index": 0,
        "codec": "h264",
        "codec_profile": "High",
        "width": 1920,
        "height": 1080,
        "resolution": "1920x1080",
        "fps": 30.0,
        "avg_fps": 30.0,
        "pixel_format": "yuv420p",
        "rotation": 0,
        "is_variable_frame_rate": false
      }
    ],
    "audio_streams": [
      {
        "index": 1,
        "codec": "aac",
        "sample_rate": 44100,
        "channels": 2,
        "channel_layout": "stereo",
        "duration_seconds": 120.5,
        "start_time_offset": 0.0
      }
    ]
  },
  "scenes": [
    {
      "scene_id": "scene_001",
      "start": 0.0,
      "end": 15.2,
      "duration": 15.2,
      "keyframe_id": "kf_001",
      "transition_type": "cut",
      "visual_summary": "Presentation slide transition (scene cut)"
    }
  ],
  "keyframes": [
    {
      "keyframe_id": "kf_001",
      "scene_id": "scene_001",
      "timestamp": 7.6,
      "frame_number": 228,
      "image_path": "keyframes/file_uuid_1234/kf_001.jpg",
      "thumbnail_path": "keyframes/file_uuid_1234/kf_001_thumb.jpg",
      "width": 1280,
      "height": 720,
      "perceptual_hash": "a1b2c3d4e5f67890",
      "ocr_text": "DocuMind AI Architecture Overview"
    }
  ],
  "tracks": [
    {
      "track_id": "track_001",
      "object_class": "person",
      "confidence": 0.88,
      "first_seen_seconds": 2.1,
      "last_seen_seconds": 14.8,
      "duration_seconds": 12.7,
      "observations": [
        {
          "frame_id": "f_63",
          "timestamp": 2.1,
          "bounding_box": [0.2, 0.4, 0.8, 0.6],
          "confidence": 0.88
        }
      ]
    }
  ],
  "timeline": [
    {
      "event_id": "evt_scene_scene_001",
      "start": 0.0,
      "end": 15.2,
      "event_type": "scene",
      "summary": "Scene #1: Presentation slide transition (scene cut)",
      "confidence": 0.95
    },
    {
      "event_id": "evt_spk_0",
      "start": 1.0,
      "end": 5.4,
      "event_type": "speech",
      "summary": "Speaker 1: Welcome to DocuMind AI video intelligence.",
      "confidence": 0.98
    }
  ],
  "transcript": "Welcome to DocuMind AI video intelligence.",
  "transcript_segments": [
    {
      "segment_id": "seg_001",
      "start": 1.0,
      "end": 5.4,
      "text": "Welcome to DocuMind AI video intelligence.",
      "speaker_id": "Speaker 1",
      "confidence": 0.98,
      "language": "en"
    }
  ],
  "speakers": ["Speaker 1"],
  "processing_status": "completed"
}
```

---

## 2. Models & Field Descriptions

### `VideoStreamInfo`
- `index` (int): Stream index within the container.
- `codec` (str): Video codec identifier (e.g. `h264`, `hevc`, `vp8`, `vp9`, `mpeg4`).
- `width` / `height` (int): Pixel dimensions.
- `resolution` (str): Formatted resolution string (e.g. `1920x1080`).
- `fps` (float): Effective frame rate.
- `pixel_format` (str): Chroma subsampling and pixel format (e.g. `yuv420p`).
- `is_variable_frame_rate` (bool): True if timestamps do not advance uniformly.

### `VideoScene`
- `scene_id` (str): Deterministic scene identifier (`scene_001`, `scene_002`).
- `start` / `end` (float): Start and end timestamps in seconds.
- `duration` (float): Scene duration in seconds.
- `transition_type` (str): Transition category (`cut` or `gradual`).
- `keyframe_id` (str): Identifier of the representative keyframe.

### `VideoTrack`
- `track_id` (str): Anonymous persistent track identifier (`track_001`).
- `object_class` (str): Classification label (`person`, `vehicle`, `object`).
- `confidence` (float): Aggregated track confidence score.
- `observations` (list[VideoObservation]): Timestamped bounding box coordinates (`[ymin, xmin, ymax, xmax]`).

### `TimelineEvent`
- `event_id` (str): Unique event identifier.
- `start` / `end` (float): Interval boundaries in seconds.
- `event_type` (str): Signal category (`scene`, `speech`, `ocr`, `visual_event`).
- `summary` (str): Human-readable event description.
- `confidence` (float): Detection confidence score.
