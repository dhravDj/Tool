# DocuMind AI — Phase 8 Performance & Benchmark Report

**Phase:** Phase 8 — Video Intelligence Engine  
**Date:** 2026-11-06T08:00:00 UTC  
**Hardware Environment:** AMD Ryzen 7 5800H (8 cores / 16 threads @ 3.2–4.4 GHz) | 16 GB DDR4 | NVIDIA RTX 3050 (4GB VRAM) | Linux Ubuntu 26.04 x86_64  
**Engine:** Python 3.13.15, OpenCV 4.11.0 / 5.0.0 headless, FFmpeg 8.0.1, FFprobe 8.0.1  

---

## 1. Executive Performance Summary

- **Total Video Fixtures Benchmarked:** 7 video recordings across MP4, MKV, MOV, AVI, and WEBM.
- **Total Video Duration Processed:** **19.06 seconds**.
- **Total Wall-Clock Processing Time:** **0.920 seconds** across all 7 fixtures.
- **Average Real-Time Factor (RTF):** **0.0482** (processing speed is **~20.7x faster than real-time playback**).
- **Fastest Processing RTF:** **0.0274** (`video_multiscene.mov`: 4.52s video analyzed in 123.92 ms).
- **Peak Process RSS Memory Footprint:** **134.22 MB** (well within the sub-500MB production constraint).
- **Incremental Frame Decoding:** Frame-by-frame memory streaming with immediate release; never buffers entire uncompressed video into RAM.

---

## 2. Granular Fixture Benchmark Breakdown

| Video Fixture | Container | Duration | Latency | RTF | Peak RSS | Scenes | Keyframes | Tracks | Timeline Events |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `video_speech_english.mp4` | MP4 | 3.0 s | 262.94 ms | 0.0876 | 131.15 MB | 2 | 2 | 1 | 7 |
| `video_speech_hindi.mkv` | MKV | 3.06 s | 217.00 ms | 0.0708 | 132.32 MB | 1 | 1 | 0 | 3 |
| `video_no_audio.mp4` | MP4 | 2.0 s | 74.09 ms | 0.0370 | 132.58 MB | 1 | 1 | 1 | 3 |
| `video_multiscene.mov` | MOV | 4.52 s | 123.92 ms | 0.0274 | 132.82 MB | 3 | 3 | 1 | 9 |
| `video_fade_transition.webm` | WEBM | 3.0 s | 93.05 ms | 0.0310 | 133.88 MB | 2 | 2 | 1 | 6 |
| `video_moving_object.avi` | AVI | 3.0 s | 83.61 ms | 0.0279 | 134.21 MB | 1 | 1 | 6 | 8 |
| `video_short_clip.mp4` | MP4 | 0.48 s | 64.91 ms | 0.1352 | 134.22 MB | 1 | 1 | 0 | 2 |

---

## 3. Computational Scaling & Resource Analysis

1. **Incremental Streaming Architecture:**
   - Decoding operates via OpenCV generator iterators yielding single frames downscaled to standard inference width (`max_dimension=720px`).
   - Frame buffers are discarded immediately after histogram computation and tracking updates, maintaining flat O(1) memory complexity with respect to video duration.
2. **Audio Demuxing Efficiency:**
   - Audio extraction uses direct FFmpeg stream piping to 16kHz mono WAV chunks, processing audio at ~50x real-time speed.
3. **Hardware Governor Safety:**
   - Multi-tenant workloads acquire execution slots in `HardwareGovernor`, bounding concurrent decoding pipelines to available physical cores.
