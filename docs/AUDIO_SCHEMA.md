# DocuMind AI — Canonical Audio Schema Specification

## 1. Schema Hierarchy

All audio intelligence operations produce and consume strongly-typed Pydantic v2 schemas defined in `app.modules.audio_intelligence.schemas.audio_document`.

```
AudioDocument
├── metadata: AudioMetadata
├── segments[]: AudioSegment
│   └── words[]: AudioWord
├── speakers[]: Speaker
├── events[]: AudioEvent
├── model_information: AudioModelInfo
└── processing_metadata: dict
```

---

## 2. Model Definitions

### 2.1 AudioMetadata
Extracted stream parameters and container tags:
- `format` (*string*): Container name, e.g. `mp3`, `wav`, `flac`, `m4a`, `ogg`, `aac`.
- `codec` (*string*): Codec identifier, e.g. `mp3`, `pcm_s16le`, `flac`, `aac`, `vorbis`.
- `duration_seconds` (*float*): Total duration of recording in seconds.
- `sample_rate` (*integer*): Audio sampling frequency in Hertz (e.g. 16000, 44100, 48000).
- `channels` (*integer*): Channel count (1=mono, 2=stereo).
- `channel_layout` (*string*): Channel configuration name, e.g. `mono`, `stereo`.
- `bit_depth` (*integer | null*): Bits per sample for uncompressed or lossless containers.
- `bitrate_kbps` (*float | null*): Stream bitrate in kbps.
- `file_size_bytes` (*integer*): File size in bytes.
- `audio_stream_count` (*integer*): Total audio streams found.
- `title`, `artist`, `album`, `genre`, `date` (*string | null*): Embedded container tags.
- `raw_tags` (*dict*): Complete dictionary of container tags.

### 2.2 AudioWord
Word-level token with precise temporal alignment:
- `word_id` (*string*): Unique token identifier, e.g. `w_abc123`.
- `text` (*string*): Spoken word text.
- `start` (*float*): Word start timestamp in seconds relative to original recording timeline.
- `end` (*float*): Word end timestamp in seconds relative to original recording timeline.
- `confidence` (*float | null*): Model token confidence score (0.0 to 1.0).

### 2.3 AudioSegment
Chronological speech segment:
- `segment_id` (*string*): Unique segment identifier, e.g. `seg_abc123`.
- `start` (*float*): Segment start timestamp in seconds.
- `end` (*float*): Segment end timestamp in seconds.
- `text` (*string*): Segment transcription text.
- `speaker_id` (*string | null*): Assigned anonymous speaker label, e.g. `Speaker 1`.
- `words` (*list[AudioWord]*): Word-level tokens.
- `confidence` (*float*): Confidence score (0.0 to 1.0).
- `source_chunk_id` (*string | null*): Processing chunk identifier if windowed.

### 2.4 Speaker
Anonymous speaker turn profile:
- `speaker_id` (*string*): Unique internal ID, e.g. `spk_1`.
- `label` (*string*): Display label, e.g. `Speaker 1`.
- `segment_ids` (*list[string]*): References to attributed `AudioSegment.segment_id`.
- `total_speaking_time_seconds` (*float*): Cumulative speaking duration.
- `metadata` (*dict*): Acoustic cluster statistics.

### 2.5 AudioEvent
Detected acoustic or environmental sound event:
- `event_id` (*string*): Unique event ID, e.g. `evt_abc123`.
- `category` (*string*): Event category: `Music`, `Silence`, `Applause`, `Environmental Noise`.
- `start` (*float*): Event start timestamp in seconds.
- `end` (*float*): Event end timestamp in seconds.
- `confidence` (*float*): Classification confidence score.
- `detection_model` (*string*): Classifier identifier.

### 2.6 AudioDocument
Master canonical container:
- `document_id` (*string*): Unique UUID.
- `source_file_id` (*string*): Ingested `FileRecord.id`.
- `format` (*string*): Audio format.
- `metadata` (*AudioMetadata*): Decoded stream parameters.
- `duration` (*float*): Duration in seconds.
- `sample_rate` (*integer*): Audio sample rate.
- `channels` (*integer*): Channel count.
- `codec` (*string*): Codec name.
- `language` (*string | null*): ISO-639-1 language code (e.g. `hi`, `en`).
- `language_confidence` (*float | null*): Language prediction confidence.
- `transcript` (*string*): Concatenated text transcript.
- `segments` (*list[AudioSegment]*): Chronological speech segments.
- `speakers` (*list[Speaker]*): Attributed speakers.
- `events` (*list[AudioEvent]*): Non-speech acoustic events.
- `processing_metadata` (*dict*): Processing duration, chunk counts.
- `model_information` (*AudioModelInfo*): Engine and model variant.
- `warnings` (*list[string]*): Quality notices.
- `confidence` (*float*): Aggregate document confidence.
- `processing_status` (*string*): `completed`, `partial`, or `failed`.
- `created_at` (*datetime*): UTC timestamp.
