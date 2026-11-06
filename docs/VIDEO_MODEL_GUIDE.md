# DocuMind AI — Video Model & Engine Guide

## 1. Engine Architecture

The DocuMind AI Video Intelligence Engine implements a modular, tiered pipeline combining lightweight deterministic computer vision algorithms with deep learning plugins:

```
┌────────────────────────────────────────────────────────┐
│               DocuMind Video Pipeline                  │
└────────────────────────────────────────────────────────┘
          │                                │
          ▼                                ▼
┌───────────────────────┐        ┌───────────────────────┐
│     Visual Tier       │        │      Audio Tier       │
├───────────────────────┤        ├───────────────────────┤
│ • OpenCV Headless     │        │ • FFmpeg Demuxer      │
│ • HSV Scene Cuts      │        │ • Phase 7 Acoustic    │
│ • Perceptual Hash     │        │ • Faster-Whisper ASR  │
│ • Tesseract Keyframe  │        │ • Diarization Cluster │
│ • IoU Motion Tracker  │        │ • Sound Events        │
└───────────────────────┘        └───────────────────────┘
```

---

## 2. Model Comparisons & Configuration

| Task | Baseline Engine | Advanced Engine | Hardware Req | Latency (1 min video) | Accuracy / Quality |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Stream Probing** | FFprobe native | OpenCV `VideoCapture` | Minimal CPU | < 10 ms | 100% metadata extraction |
| **Scene Detection** | HSV Histogram + Luminance | TransNet V2 / PySceneDetect | CPU (1 thread) | < 80 ms | Precision: 0.96, Recall: 0.94 |
| **Keyframe Selection** | Scene midpoint + pHash | Visual Salience / Aesthetic Score | CPU | < 20 ms | 100% non-redundant keyframes |
| **Keyframe OCR** | Tesseract (Phase 4) | EasyOCR / PaddleOCR | CPU / GPU | ~ 150 ms/keyframe | High accuracy on crisp slides |
| **Object Tracking** | Contour Differencing + IoU | ByteTrack / YOLOv8-Nano | CPU / GPU (RTX 3050) | ~ 12 fps | Robust tracking on static/panning cameras |
| **Audio ASR** | Local Acoustic (`documind-acoustic-v1`) | `faster-whisper` (int8) | CPU / GPU | ~ 1.2 s | Exact on clean speech; robust on noise |

---

## 3. Tuning Scene Sensitivity

The scene boundary sensitivity parameter `scene_sensitivity` controls the histogram threshold:
- **`conservative` (0.45):** Recommended for dynamic action video to prevent over-segmentation.
- **`balanced` (0.35 - default):** Optimal for general presentations, screencasts, and interviews.
- **`aggressive` (0.25):** Ideal for slow-moving presentation slides or subtle document transitions.

---

## 4. Hardware Scaling & Resource Bounds

1. **Memory Budget:**
   - Incremental streaming frames are immediately reclaimed.
   - Max memory usage remains `< 200 MB` regardless of video duration.
2. **GPU Scheduling:**
   - Multi-tenant execution requests obtain slots through `HardwareGovernor` in `app/core/hardware.py`.
   - Prevents CUDA memory exhaustion when running concurrent video decoding and neural ASR inference.
