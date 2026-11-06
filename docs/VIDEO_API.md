# DocuMind AI — Video Intelligence REST API Specification

## Base URLs
- Platform Base URL: `/api/v1`
- Video Intelligence Root: `/api/v1/video-intelligence`
- File Video Analysis Root: `/api/v1/files/{file_id}/video-analysis`

---

## 1. Endpoints

### 1.1 `GET /api/v1/video-intelligence/capabilities`
Returns current system capabilities, supported video formats, installed engines, and hardware configuration.

**Response:**
```json
{
  "supported_formats": ["avi", "mkv", "mov", "mp4", "webm"],
  "max_duration_seconds": 3600,
  "max_file_size_bytes": 524288000,
  "installed_engines": ["documind-video-v1", "tesseract", "documind-motion-v1", "documind-acoustic-v1"],
  "active_engine": "documind-video-v1",
  "scene_detection_available": true,
  "ocr_available": true,
  "tracking_available": true,
  "audio_integration_available": true,
  "hardware": {
    "governor_active": true,
    "max_workers": 4,
    "gpu_slots": 1
  }
}
```

---

### 1.2 `GET /api/v1/video-intelligence/supported-formats`
Returns a list of supported video container formats and codecs.

---

### 1.3 `POST /api/v1/video-intelligence/analyze`
Submits a video file for full asynchronous or synchronous video intelligence analysis.

**Request Body:**
```json
{
  "file_id": "file_uuid_1234",
  "options": {
    "scene_sensitivity": 0.35,
    "max_keyframes_per_scene": 1,
    "run_ocr": true,
    "run_tracking": true,
    "run_audio": true
  }
}
```

---

### 1.4 `GET /api/v1/files/{file_id}/video-document`
Retrieves the complete canonical `VideoDocument` for a previously analyzed video file.

---

### 1.5 `GET /api/v1/files/{file_id}/video-analysis/summary`
Returns high-level video metrics (duration, resolution, fps, scene count, keyframe count, track count, transcript preview).

---

### 1.6 `GET /api/v1/files/{file_id}/video-analysis/scenes`
Returns the list of detected video scenes with start/end timestamps and transition types.

---

### 1.7 `GET /api/v1/files/{file_id}/video-analysis/keyframes`
Returns all extracted keyframes with timestamps, bounding dimensions, and perceptual hashes.

---

### 1.8 `GET /api/v1/files/{file_id}/video-analysis/tracks`
Returns continuous object tracks with observation sequences and bounding boxes.

---

### 1.9 `GET /api/v1/files/{file_id}/video-analysis/ocr`
Returns all OCR text blocks extracted across scene keyframes.

---

### 1.10 `GET /api/v1/files/{file_id}/video-analysis/timeline`
Returns the unified chronological multimodal timeline combining visual, audio, OCR, and event signals.

---

### 1.11 `GET /api/v1/files/{file_id}/video-analysis/transcript`
Returns the synchronized speech transcript segments with speaker attribution.

---

### 1.12 `GET /api/v1/files/{file_id}/video-analysis/export/{format}`
Streams or downloads exported representations of the video intelligence document.
- `format`: `json`, `markdown`, `text`, `srt`, `vtt`, `manifest`, `keyframes_manifest`.

---

### 1.13 `GET /api/v1/files/{file_id}/video-analysis/keyframe/{keyframe_id}/image`
Streams the JPEG image asset for a specific keyframe. Supports query parameter `thumbnail=true` for 256px thumbnails.
