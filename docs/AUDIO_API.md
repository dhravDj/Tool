# DocuMind AI — Audio Intelligence API Reference

All audio intelligence endpoints are routed under `/api/v1` and follow standard DocuMind AI response envelopes (`APIResponse[T]`).

---

## 1. Capabilities & Model Discovery

### GET `/api/v1/audio-intelligence/capabilities`
Returns system audio capabilities, supported formats, limits, and active speech engines.

**Response:**
```json
{
  "success": true,
  "data": {
    "supported_formats": ["aac", "flac", "m4a", "mp3", "ogg", "wav"],
    "max_duration_seconds": 7200.0,
    "max_file_size_bytes": 104857600,
    "installed_engines": ["documind-acoustic"],
    "active_engine": "documind-acoustic",
    "diarization_available": true,
    "sound_events_available": true,
    "hardware": {
      "governor_active": true,
      "max_workers": 4,
      "gpu_slots": 1
    }
  }
}
```

### GET `/api/v1/audio-intelligence/models`
Returns list of speech recognition engines, installed models, and VRAM/RAM footprints.

---

## 2. Audio Analysis Endpoints

### POST `/api/v1/files/{file_id}/analyze-audio`
Triggers full end-to-end audio processing: probing, resampling, transcription, diarization, sound event classification, artifact generation, and database persistence.

**Request Body (optional):**
```json
{
  "engine": "documind-acoustic",
  "language": "hi",
  "prompt": "Custom vocabulary or context prompt"
}
```

**Response:** Returns `AudioManifest` with execution statistics and artifact URLs.

---

### GET `/api/v1/files/{file_id}/audio-analysis`
Returns high-level analysis summary record from PostgreSQL.

### GET `/api/v1/files/{file_id}/audio-analysis/result`
Retrieves complete canonical `AudioDocument` including all segments, words, speakers, and events from artifact storage.

### GET `/api/v1/files/{file_id}/audio-analysis/transcript`
Retrieves full text transcript, detected language, and word count.

### GET `/api/v1/files/{file_id}/audio-analysis/segments?q={search_term}`
Retrieves timestamped speech segments with optional case-insensitive text search.

### GET `/api/v1/files/{file_id}/audio-analysis/speakers`
Retrieves anonymous speaker profiles, turn counts, and speaking duration.

### GET `/api/v1/files/{file_id}/audio-analysis/events`
Retrieves detected non-speech acoustic sound events (`Music`, `Silence`, `Applause`, `Environmental Noise`).

### GET `/api/v1/files/{file_id}/audio-analysis/summary`
Retrieves brief executive summary.

---

## 3. Export Endpoints

### GET `/api/v1/files/{file_id}/audio-analysis/export/{format}`
Exports the analyzed audio transcription in one of 5 supported formats:
- `srt`: Standard SubRip subtitle format (`00:00:01,000 --> 00:00:04,500`).
- `vtt`: W3C WebVTT format (`WEBVTT`).
- `md` or `markdown`: Executive Markdown report.
- `txt`: Plain text transcript.
- `json`: Canonical `AudioDocument` JSON.
