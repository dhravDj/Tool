# DocuMind AI — Phase 7 Performance & Benchmark Report

**Phase:** Phase 7 — Audio Intelligence  
**Date:** 2026-11-06T07:25:00 UTC  
**Hardware Environment:** AMD Ryzen 7 5800H (8 cores / 16 threads @ 3.2–4.4 GHz) | 16 GB DDR4 | NVIDIA RTX 3050 (4GB VRAM) | Linux Ubuntu 26.04 x86_64  
**Engine:** Python 3.13.15, `soundfile` 0.14.0, `mutagen` 1.48.1, `ffmpeg` 8.0.1  

---

## 1. Executive Performance Summary

- **Total Audio Fixtures Benchmarked:** 11 recordings across MP3, WAV, M4A, AAC, FLAC, and OGG.
- **Total Audio Duration Processed:** **66.61 seconds**.
- **Total Wall-Clock Processing Time:** **1.174 seconds**.
- **Average Real-Time Factor (RTF):** **0.0176** (processing speed is **~57x faster than real-time**).
- **Fastest Processing RTF:** **0.0066** (`long_recording.wav` 35.0s audio processed in 231.27 ms).
- **Peak Process RSS Memory Footprint:** **89.77 MB**.
- **Hardware Acceleration:** Native CPU execution bounded by `HardwareGovernor` (max 4 parallel workers).

---

## 2. Granular Fixture Benchmark Breakdown

| Audio Fixture | Format | Duration | Processing Latency | RTF | Peak RSS | Acoustic Features Processed |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `speech_english.wav` | WAV | 3.0 s | 127.26 ms | 0.0424 | 85.60 MB | English speech, 16kHz mono, word alignment |
| `speech_hindi.wav` | WAV | 3.5 s | 127.97 ms | 0.0366 | 86.27 MB | Hindi Devanagari Unicode, 44.1kHz stereo |
| `speech_hinglish.mp3` | MP3 | 4.0 s | 86.81 ms | 0.0217 | 86.41 MB | Hinglish code-switching, 48kHz ID3 tags |
| `conversation_multispeaker.wav` | WAV | 6.0 s | 89.51 ms | 0.0149 | 86.92 MB | Multi-speaker dialogue, 2 speaker clusters |
| `speech_lossless.flac` | FLAC | 2.5 s | 90.23 ms | 0.0361 | 86.93 MB | Lossless audio, Vorbis comments |
| `speech_vorbis.ogg` | OGG | 2.5 s | 84.61 ms | 0.0338 | 86.94 MB | Ogg stream decoding, Vorbis tags |
| `speech_m4a.m4a` | M4A | 3.0 s | 82.84 ms | 0.0276 | 86.94 MB | ISO-BMFF container, AAC audio |
| `speech_adts.aac` | AAC | 2.11 s | 85.19 ms | 0.0403 | 86.94 MB | Raw ADTS stream, sync frame validation |
| `long_recording.wav` | WAV | 35.0 s | 231.27 ms | 0.0066 | 89.75 MB | 2 windowed chunks, VAD silence boundaries |
| `pure_silence.wav` | WAV | 2.0 s | 82.79 ms | 0.0414 | 89.76 MB | Silence detection, non-speech classification |
| `harmonic_music.mp3` | MP3 | 3.0 s | 85.29 ms | 0.0284 | 89.77 MB | Harmonic music event classification |

---

## 3. Resource & Scaling Analysis

1. **Sub-100MB Memory Overhead:**
   - The entire pipeline operates with peak process RSS memory of **89.77 MB**.
   - Processing long recordings uses windowed chunking and temporary files cleaned up on exit.
2. **Real-Time Factor (RTF):**
   - At 0.0176 RTF, an hour of audio (3600 seconds) processes in under 65 seconds on CPU.
3. **Hardware Governor Protection:**
   - Tasks acquire bounded slots in `HardwareGovernor`, preventing CPU starvation and ensuring zero CUDA OOM errors.
