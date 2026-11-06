# DocuMind AI — Video Intelligence Engine Architecture

## 1. System Overview

Phase 8 introduces the **Video Intelligence Engine** into DocuMind AI. The engine ingests, probes, decodes, segments, tracks, transcribes, and indexes video recordings across 5 major formats (**MP4, MKV, MOV, AVI, and WEBM**) into structured, searchable timestamped documents.

```
Uploaded Video (.mp4, .mkv, .mov, .avi, .webm)
                     │
                     ▼
       Universal File Detection Engine (Phase 2)
  (MIME, magic sync bytes, container headers: ISOBMFF, EBML, RIFF)
                     │
                     ▼
           VideoPreprocessor
  - ffprobe stream inspection & container metadata probing
  - OpenCV fallback stream inspection
  - FFmpeg 16kHz mono 16-bit PCM audio extraction
  - Audio start-offset compensation (PTS)
                     │
                     ▼
             VideoDecoder
  - Incremental frame streaming with PTS timestamps
  - Resolution scaling (max_dimension=720px)
  - VFR handling & monotonic timestamp assignment
  - Bounded memory consumption (O(1) memory complexity)
                     │
                     ▼
            SceneDetector
  - Perceptual HSV histogram comparison & luminance delta
  - Hard cuts & gradual fade transitions
  - Configurable sensitivity (conservative, balanced, aggressive)
                     │
                     ▼
          KeyframeExtractor
  - Representative midpoint scene frame extraction
  - Thumbnail generation & perceptual hash deduplication
  - LocalStorageService asset persistence
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
 ImageOCREngine              ObjectTracker
(Tesseract Keyframe OCR)    (Motion / Contours & IoU Multi-frame Tracking)
       │                           │
       └─────────────┬─────────────┘
                     ▼
          VisualEventDetector
  - Scene transitions, person motion, presentation slides
                     │
                     ▼
        Phase 7 Audio Intelligence
  - Speech transcription (English, Hindi Devanagari Unicode)
  - Word timestamps & speaker diarization
                     │
                     ▼
      MultimodalTimelineBuilder
  - Unified chronological timeline (seconds precision)
  - Scenes, keyframes, OCR, tracks, visual events, speech
                     │
                     ▼
          Canonical VideoDocument
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
7 Export Formats   PostgreSQL 16   FastAPI Endpoints &
(JSON, MD, TXT,   (Alembic 007)   Interactive React Player
SRT, VTT, Manifests)
```

---

## 2. Key Capabilities

### 2.1 Multi-Signal Container Detection
- **MP4:** ISO-BMFF container detection checking `ftyp` brand signatures (`mp41`, `mp42`, `isom`, `iso2`, `avc1`).
- **MOV:** Apple QuickTime container detection checking `moov`, `wide`, or `qt  ` brands.
- **MKV:** Extensible Binary Meta Language (EBML) header (`0x1A45DFA3`) with `matroska` DocType.
- **WEBM:** EBML header with `webm` DocType.
- **AVI:** RIFF container with `AVI ` format chunk.

### 2.2 Controlled Incremental Decoding
- **Memory Safety:** Streaming frame iteration yields single frames downscaled to target inference resolution (`max_dimension=720px`). Frames are processed and deallocated immediately, maintaining peak RSS memory around **134 MB**.
- **Presentation Timestamps (PTS):** High-precision millisecond-accurate timestamps assigned to each frame, accommodating variable frame rates (VFR).

### 2.3 Scene Detection & Keyframe Deduplication
- **Boundary Detection:** Evaluates consecutive frame differences using normalized HSV color histograms and average luminance deltas.
- **Transition Types:** Distinguishes between instantaneous hard cuts and gradual fade-to-black/fade-in transitions.
- **Perceptual Hash Deduplication:** Extracts representative midpoint scene keyframes and discards visually identical frames using average hash difference scoring.

### 2.4 OCR & Object Tracking
- **Keyframe OCR:** Leverages the Phase 4 `ImageOCREngine` (Tesseract) on keyframe images to extract text from slides, banners, and on-screen graphics.
- **Motion & Contour Tracking:** Employs frame differencing, background subtraction, and contour bounding boxes.
- **IoU Multi-Frame Association:** Connects detections across consecutive frames via Intersection over Union (IoU) matching, assigning persistent anonymous IDs (`track_001`, `track_002`) and recording bounding box trajectories.

### 2.5 Audio Extraction & Multimodal Synchronization
- **Audio Demuxing:** FFmpeg extracts 16kHz mono audio from video containers while measuring `start_time_offset`.
- **Phase 7 Integration:** Dispatches extracted audio to `AudioIntelligencePipeline`, generating speech transcripts, speaker diarization, and sound event tags.
- **Timeline Alignment:** Audio utterance timestamps are offset-compensated and merged into a master chronological timeline alongside visual events.

---

## 3. Database Persistence & Storage

- Model `VideoAnalysisRecord` in `backend/app/infrastructure/database/models.py`.
- Reversible Alembic migration `007_video_analysis_records.py`.
- Keyframe full-resolution images and thumbnails saved into the configured local storage directory under `keyframes/{file_id}/`.
