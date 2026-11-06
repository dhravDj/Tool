"""Canonical Pydantic v2 schemas for Audio Intelligence Engine."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AudioMetadata(BaseModel):
    """Extracted audio stream metadata and container tags."""

    format: str = Field(..., description="Audio container or format name, e.g. mp3, wav, flac")
    codec: str = Field(..., description="Audio codec identifier, e.g. mp3, pcm_s16le, flac, aac, vorbis")
    duration_seconds: float = Field(default=0.0, description="Total duration of audio in seconds")
    sample_rate: int = Field(default=0, description="Audio sampling rate in Hertz (e.g. 44100, 48000, 16000)")
    channels: int = Field(default=1, description="Number of audio channels (1=mono, 2=stereo, etc.)")
    channel_layout: str = Field(default="mono", description="Channel layout name (mono, stereo, 5.1, etc.)")
    bit_depth: int | None = Field(default=None, description="Audio bit depth if uncompressed or lossless (e.g. 16, 24)")
    bitrate_kbps: float | None = Field(default=None, description="Average or constant bitrate in kilobits per second")
    file_size_bytes: int = Field(default=0, description="Physical size of audio file in bytes")
    audio_stream_count: int = Field(default=1, description="Number of audio streams in media container")
    title: str | None = Field(default=None, description="Embedded track title if present in tags")
    artist: str | None = Field(default=None, description="Embedded artist or creator name if present")
    album: str | None = Field(default=None, description="Embedded album name if present")
    genre: str | None = Field(default=None, description="Embedded musical or audio genre")
    date: str | None = Field(default=None, description="Embedded creation date or year")
    raw_tags: dict[str, Any] = Field(default_factory=dict, description="Raw tag dictionary extracted from container")


class AudioWord(BaseModel):
    """Precise word-level transcription with alignment timestamps."""

    word_id: str = Field(default_factory=lambda: f"w_{uuid.uuid4().hex[:8]}")
    text: str = Field(..., description="Spoken word token")
    start: float = Field(..., description="Start timestamp in seconds relative to original audio timeline")
    end: float = Field(..., description="End timestamp in seconds relative to original audio timeline")
    confidence: float | None = Field(default=None, description="Acoustic or model token confidence score (0.0 to 1.0)")


class AudioSegment(BaseModel):
    """Chronological speech segment with timestamps and speaker attribution."""

    segment_id: str = Field(default_factory=lambda: f"seg_{uuid.uuid4().hex[:8]}")
    start: float = Field(..., description="Start timestamp in seconds relative to original audio timeline")
    end: float = Field(..., description="End timestamp in seconds relative to original audio timeline")
    text: str = Field(..., description="Transcribed text for this segment")
    speaker_id: str | None = Field(default=None, description="Assigned anonymous speaker ID, e.g. 'Speaker 1'")
    words: list[AudioWord] = Field(default_factory=list, description="Word-level tokens if alignment supported")
    confidence: float = Field(default=1.0, description="Segment transcription confidence score (0.0 to 1.0)")
    source_chunk_id: str | None = Field(default=None, description="Identifier of processing chunk if windowed")


class Speaker(BaseModel):
    """Anonymous speaker turn profile and utterance list."""

    speaker_id: str = Field(..., description="Unique speaker label, e.g. 'spk_1'")
    label: str = Field(..., description="Human-readable speaker display label, e.g. 'Speaker 1'")
    segment_ids: list[str] = Field(default_factory=list, description="IDs of segments spoken by this speaker")
    total_speaking_time_seconds: float = Field(default=0.0, description="Total speaking time in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Acoustic characteristics or cluster info")


class AudioEvent(BaseModel):
    """Detected acoustic or environmental sound event."""

    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    category: str = Field(..., description="Event category, e.g. Music, Applause, Laughter, Silence, Noise")
    start: float = Field(..., description="Event start timestamp in seconds relative to original audio timeline")
    end: float = Field(..., description="Event end timestamp in seconds relative to original audio timeline")
    confidence: float = Field(default=1.0, description="Detection confidence score (0.0 to 1.0)")
    detection_model: str = Field(default="documind-acoustic-v1", description="Model or classifier used")


class AudioModelInfo(BaseModel):
    """Details regarding speech-to-text and acoustic models used."""

    engine_name: str = Field(default="documind-acoustic", description="ASR engine or backend identifier")
    model_name: str = Field(default="documind-acoustic-v1", description="Specific model variant or size")
    device: str = Field(default="cpu", description="Execution hardware: cpu, cuda, or cloud")
    quantization: str | None = Field(default=None, description="Model quantization if applicable, e.g. int8, float16")
    is_heuristic: bool = Field(default=False, description="True if heuristic/local acoustic baseline was used")


class AudioDocument(BaseModel):
    """Canonical, strongly-typed representation of an analyzed audio recording."""

    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_file_id: str = Field(..., description="Reference to uploaded FileRecord ID")
    format: str = Field(..., description="Audio format, e.g. mp3, wav, m4a, aac, flac, ogg")
    metadata: AudioMetadata = Field(..., description="Decoded stream and container metadata")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Sampling rate in Hertz")
    channels: int = Field(..., description="Channel count")
    codec: str = Field(..., description="Audio codec")
    language: str | None = Field(default=None, description="Detected or specified ISO language code (e.g. hi, en)")
    language_confidence: float | None = Field(default=None, description="Confidence of language identification")
    transcript: str = Field(default="", description="Full concatenated text transcript")
    segments: list[AudioSegment] = Field(default_factory=list, description="Chronological speech segments")
    speakers: list[Speaker] = Field(default_factory=list, description="Identified anonymous speakers")
    events: list[AudioEvent] = Field(default_factory=list, description="Detected sound and environmental events")
    processing_metadata: dict[str, Any] = Field(default_factory=dict, description="Execution timing and chunk metrics")
    model_information: AudioModelInfo = Field(default_factory=AudioModelInfo, description="AI models and engine details")
    warnings: list[str] = Field(default_factory=list, description="Pipeline warnings or quality advisories")
    confidence: float = Field(default=1.0, description="Overall document confidence score (0.0 to 1.0)")
    processing_status: str = Field(default="completed", description="Status: completed, partial, or failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AudioManifest(BaseModel):
    """Audit manifest detailing execution provenance and generated outputs."""

    document_id: str
    file_id: str
    source_filename: str
    source_format: str
    status: str
    engine_name: str
    model_name: str
    processing_time_seconds: float
    duration_seconds: float
    detected_language: str | None
    segment_count: int
    word_count: int
    speaker_count: int
    event_count: int
    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AudioCapabilities(BaseModel):
    """Runtime capabilities and available models of the Audio Intelligence subsystem."""

    supported_formats: list[str]
    max_duration_seconds: float
    max_file_size_bytes: int
    installed_engines: list[str]
    active_engine: str
    diarization_available: bool
    sound_events_available: bool
    hardware: dict[str, Any]
