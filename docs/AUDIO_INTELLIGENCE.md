# DocuMind AI — Audio Intelligence Engine Architecture

## 1. System Overview

Phase 7 introduces the **Audio Intelligence Engine** into DocuMind AI. The engine ingests, probes, decodes, resamples, transcribes, diarizes, and indexes audio recordings across 6 formats (**MP3, WAV, M4A, AAC, FLAC, and OGG**) into structured, searchable timestamped documents.

```
Uploaded Audio (.mp3, .wav, .m4a, .aac, .flac, .ogg)
                     │
                     ▼
       Universal File Detection Engine (Phase 2)
  (MIME, magic sync bytes, container headers)
                     │
                     ▼
          AudioPreprocessor
  - ffprobe stream inspection & mutagen container tags
  - FFmpeg 16kHz mono 16-bit PCM resampling
  - Energy amplitude & dynamic range calculation
  - Silence boundary & VAD chunking (30s windows)
                     │
                     ▼
        AudioTranscriptionRouter
  (Bounded by HardwareGovernor: max 4 CPU, 1 GPU)
   ┌─────────────────┼─────────────────┐
   ▼                 ▼                 ▼
Local Acoustic    faster-whisper    whisper.cpp
Baseline          (CTranslate2)     (Compiled CLI)
                     │
                     ▼
          AudioDiarizer
  - Spectral centroid & zero-crossing rate clustering
  - Anonymous labels: "Speaker 1", "Speaker 2"
                     │
                     ▼
        SoundEventDetector
  - Harmonic content (Music)
  - Low RMS (Silence)
  - Spectral flatness & burst energy (Applause, Noise)
                     │
                     ▼
         Canonical AudioDocument
   ┌─────────────────┼─────────────────┐
   ▼                 ▼                 ▼
6 Output Formats  PostgreSQL 16    FastAPI Endpoints &
(JSON, MD, TXT,   (Alembic 006)    Interactive React Player
SRT, VTT, Manifest)
```

---

## 2. Key Capabilities

### 2.1 Multi-Signal Format Detection
- **MP3:** ID3v2 container headers (`ID3`) and raw MPEG-1/2 Audio Layer III sync words (`0xFFFB`, `0xFFF3`, `0xFFF2`) with layer `01` bitmask validation.
- **WAV:** RIFF container structure with `WAVE` form tag at offset 8.
- **FLAC:** Native bit-perfect signature `fLaC` at offset 0.
- **OGG:** Xiph.Org Ogg bitstream container header `OggS` at offset 0.
- **M4A:** ISO Base Media File Format (`ftyp`) with major brands `m4a `, `m4b `, or `m4p `.
- **AAC:** Raw ADTS frame headers (`0xFFF0` with layer `00` bitmask `0xFFF6`).

### 2.2 Controlled Preprocessing & VAD Chunking
- **Decoding & Resampling:** Utilizes native FFmpeg decoding into standardized 16,000 Hz, mono, 16-bit signed PCM WAV.
- **Amplitude Inspection:** Analyzes RMS energy, peak amplitude, and dynamic range in decibels ($20 \log_{10}(\text{peak}/\text{rms})$).
- **VAD & Silence Detection:** Uses FFmpeg `silencedetect` and acoustic energy thresholds to identify speech vs silence intervals.
- **Windowed Slicing for Long Audio:** Recordings exceeding 30 seconds are partitioned at silence midpoints with configurable overlap (1.0s), preventing mid-sentence clipping while strictly maintaining exact timestamp mappings back to the master audio timeline.

### 2.3 Speech Recognition & Multilingualism
- **Local Acoustic Engine (`documind-acoustic-v1`):** Fast, sovereign baseline engine that extracts speech boundaries, embedded transcripts/lyrics tags, and generates aligned word timestamps with zero network downloads.
- **Neural Backends:** Pluggable support for `faster-whisper` (CTranslate2) and `whisper.cpp`.
- **Multilingual Support:** Auto-detection and explicit language selection for Hindi, English, and Hinglish code-switching. Preserves Devanagari Unicode without forced English translation.

### 2.4 Anonymous Speaker Diarization
- **Privacy First:** Never attempts to identify real people or store biometric voiceprints.
- **Turn Attribution:** Assigns anonymous identifiers (`Speaker 1`, `Speaker 2`) using acoustic timbre clustering (spectral centroid, roll-off, zero-crossing rate) and text turn cues.

### 2.5 Sound Event Classification
- Separate detection of non-speech acoustic events: `Music`, `Silence`, `Applause`, and `Environmental Noise`. Stored in `AudioDocument.events` separate from speech transcripts.

---

## 3. Hardware Governance & Memory Management

Optimized for **AMD Ryzen 7 5800H** and **NVIDIA RTX 3050 (4GB VRAM)**:
1. **CPU Throttling:** Concurrency bounded via `HardwareGovernor.cpu_bound_slot()` (`MAX_PARALLEL_WORKERS = 4`).
2. **GPU Mutex:** Strict mutual exclusion via `HardwareGovernor.gpu_bound_slot()` (`GPU_MAX_CONCURRENT_INFERENCE = 1`) to eliminate CUDA OOM faults.
3. **Quantization:** Support for `int8` quantization in CTranslate2, allowing Whisper `base` and `small` models to execute safely within 4GB VRAM.
