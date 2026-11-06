"""Canonical Pydantic v2 schemas for DocuMind AI Phase 8: Video Intelligence."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioEvent,
    AudioSegment,
    Speaker,
)


class VideoStreamInfo(BaseModel):
    """Detailed metadata for an individual video stream."""

    index: int = 0
    codec: str = "unknown"
    codec_profile: str = ""
    width: int = 0
    height: int = 0
    resolution: str = "0x0"
    fps: float = 0.0
    avg_fps: float = 0.0
    pixel_format: str = "yuv420p"
    bit_depth: int | None = None
    color_space: str | None = None
    aspect_ratio: str | None = None
    rotation: int = 0
    frame_count: int | None = None
    bitrate_kbps: float | None = None
    is_variable_frame_rate: bool = False


class AudioStreamInfo(BaseModel):
    """Detailed metadata for an individual audio stream inside the video container."""

    index: int = 0
    codec: str = "unknown"
    sample_rate: int = 0
    channels: int = 1
    channel_layout: str = "mono"
    bitrate_kbps: float | None = None
    duration_seconds: float | None = None
    language: str | None = None
    start_time_offset: float = 0.0


class VideoMetadata(BaseModel):
    """Global multimedia container and stream metadata."""

    filename: str = ""
    container_format: str = "unknown"
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    bitrate_kbps: float | None = None
    stream_count: int = 1
    creation_time: str | None = None
    tags: dict[str, Any] = Field(default_factory=dict)
    video_streams: list[VideoStreamInfo] = Field(default_factory=list)
    audio_streams: list[AudioStreamInfo] = Field(default_factory=list)


class VideoDetection(BaseModel):
    """Visual object detected in a specific frame."""

    detection_id: str = Field(default_factory=lambda: f"det_{uuid.uuid4().hex[:8]}")
    frame_id: str
    timestamp: float
    object_class: str
    bounding_box: list[float]  # [ymin, xmin, ymax, xmax] normalized [0, 1]
    confidence: float = 1.0
    track_id: str | None = None


class VideoObservation(BaseModel):
    """Time-indexed observation of a tracked object."""

    frame_id: str
    timestamp: float
    bounding_box: list[float]
    confidence: float = 1.0


class VideoTrack(BaseModel):
    """Continuous temporal trajectory of an anonymous object across video frames."""

    track_id: str = Field(default_factory=lambda: f"track_{uuid.uuid4().hex[:8]}")
    object_class: str
    first_seen_seconds: float
    last_seen_seconds: float
    duration_seconds: float
    confidence: float = 1.0
    observations: list[VideoObservation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VideoOCRResult(BaseModel):
    """On-screen text recognized within a video frame."""

    ocr_id: str = Field(default_factory=lambda: f"ocr_{uuid.uuid4().hex[:8]}")
    text: str
    bounding_box: list[float]  # [ymin, xmin, ymax, xmax] normalized [0, 1]
    confidence: float = 1.0
    engine: str = "tesseract"


class VideoFrame(BaseModel):
    """Sampled or representative video frame with visual intelligence annotations."""

    frame_id: str = Field(default_factory=lambda: f"frm_{uuid.uuid4().hex[:8]}")
    timestamp: float
    frame_index: int
    asset_reference: str
    thumbnail_reference: str | None = None
    width: int
    height: int
    content_hash: str
    ocr_results: list[VideoOCRResult] = Field(default_factory=list)
    detections: list[VideoDetection] = Field(default_factory=list)
    description: str = ""
    scene_type: str = "unknown"
    dominant_colors: list[str] = Field(default_factory=list)


class VideoKeyframe(BaseModel):
    """Representative keyframe for a scene."""

    keyframe_id: str = Field(default_factory=lambda: f"key_{uuid.uuid4().hex[:8]}")
    scene_id: str
    frame_id: str
    timestamp: float
    position_type: str = "scene_middle"  # scene_start, scene_middle, scene_end, sampled
    asset_reference: str
    thumbnail_reference: str
    summary: str = ""


class VideoEvent(BaseModel):
    """Temporal visual activity or physical scene transition."""

    event_id: str = Field(default_factory=lambda: f"vev_{uuid.uuid4().hex[:8]}")
    category: str  # person_movement, scene_transition, presentation_slide, camera_motion, object_entry_exit, general_activity
    start: float
    end: float
    description: str
    scene_id: str | None = None
    related_frame_ids: list[str] = Field(default_factory=list)
    related_track_ids: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    detection_engine: str = "documind-motion-v1"


class VideoScene(BaseModel):
    """Temporal visual scene segmented by boundary detection."""

    scene_id: str = Field(default_factory=lambda: f"scene_{uuid.uuid4().hex[:8]}")
    start: float
    end: float
    duration: float
    start_frame: int = 0
    end_frame: int = 0
    representative_keyframe_id: str = ""
    frame_references: list[str] = Field(default_factory=list)
    visual_summary: str = ""
    transition_type: str = "cut"  # cut, fade, dissolve, continuous
    confidence: float = 1.0
    related_events: list[str] = Field(default_factory=list)
    transcript_snippets: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """Unified multimodal temporal event connecting audio, video, OCR and scene changes."""

    event_id: str = Field(default_factory=lambda: f"tle_{uuid.uuid4().hex[:8]}")
    event_type: str  # scene, keyframe, ocr, object_track, visual_event, speech, speaker_turn, audio_event
    start: float
    end: float
    label: str
    summary: str
    source_reference: str
    related_entities: list[str] = Field(default_factory=list)


class VideoModelInfo(BaseModel):
    """Provenance and runtime execution environment for video intelligence."""

    engine_name: str = "documind-video"
    model_name: str = "documind-video-v1"
    device: str = "cpu"
    is_heuristic: bool = True
    ocr_engine: str = "tesseract"
    audio_engine: str | None = None


class VideoDocument(BaseModel):
    """Root canonical representation of an analyzed video file."""

    document_id: str = Field(default_factory=lambda: f"vdoc_{uuid.uuid4().hex}")
    source_file_id: str
    format: str
    metadata: VideoMetadata
    duration: float
    video_streams: list[VideoStreamInfo] = Field(default_factory=list)
    audio_streams: list[AudioStreamInfo] = Field(default_factory=list)
    scenes: list[VideoScene] = Field(default_factory=list)
    keyframes: list[VideoKeyframe] = Field(default_factory=list)
    frames: list[VideoFrame] = Field(default_factory=list)
    detections: list[VideoDetection] = Field(default_factory=list)
    tracks: list[VideoTrack] = Field(default_factory=list)
    visual_events: list[VideoEvent] = Field(default_factory=list)
    transcript: str = ""
    speakers: list[Speaker] = Field(default_factory=list)
    transcript_segments: list[AudioSegment] = Field(default_factory=list)
    audio_events: list[AudioEvent] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
    model_information: VideoModelInfo = Field(default_factory=VideoModelInfo)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    processing_status: str = "completed"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class VideoManifest(BaseModel):
    """Audit manifest of video intelligence artifacts and execution parameters."""

    document_id: str
    file_id: str
    source_filename: str
    source_format: str
    status: str = "completed"
    engine_name: str
    model_name: str
    processing_time_seconds: float
    duration_seconds: float
    scene_count: int = 0
    keyframe_count: int = 0
    detection_count: int = 0
    track_count: int = 0
    transcript_word_count: int = 0
    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class VideoCapabilities(BaseModel):
    """System-level video intelligence capabilities and hardware acceleration status."""

    supported_formats: list[str]
    max_duration_seconds: int
    max_file_size_bytes: int
    installed_engines: list[str]
    active_engine: str
    scene_detection_available: bool
    ocr_available: bool
    tracking_available: bool
    audio_integration_available: bool
    hardware: dict[str, Any] = Field(default_factory=dict)
