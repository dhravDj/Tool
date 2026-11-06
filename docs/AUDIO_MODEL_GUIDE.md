# DocuMind AI — Audio & Speech Model Selection Guide

## 1. Supported Inference Backends

DocuMind AI provides a tiered speech recognition architecture designed around hardware sovereignty, local execution, and constrained memory budgets (e.g. 4GB VRAM).

| Engine / Backend | Default Model | Hardware Target | VRAM Footprint | RAM Footprint | Typical RTF |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`documind-acoustic`** | `documind-acoustic-v1` | CPU (All platforms) | 0 MB | ~50 MB | **0.017x** (58x real-time) |
| **`faster-whisper`** | `base` (int8) | CPU / NVIDIA RTX 3050 | ~500 MB | ~800 MB | ~0.15x (6x real-time) |
| **`faster-whisper`** | `small` (int8) | NVIDIA RTX 3050 (4GB) | ~1.5 GB | ~2.0 GB | ~0.35x (3x real-time) |
| **`whisper-cpp`** | `base.bin` | CPU (Native C/C++) | 0 MB | ~400 MB | ~0.20x (5x real-time) |
| **`cloud`** (Optional) | `gemini-2.5-flash` | Cloud API | 0 MB | 0 MB | ~0.50x |

---

## 2. Hardware Resource Constraints (RTX 3050 4GB VRAM)

The development host features:
- **CPU:** AMD Ryzen 7 5800H (8 physical cores / 16 threads @ 3.2–4.4 GHz)
- **RAM:** 16 GB DDR4
- **GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)

### Guidelines:
1. **Never load `whisper-large` or `whisper-large-v3` on 4GB VRAM.** Large models consume >3.2 GB VRAM in float16, causing immediate Out-Of-Memory (OOM) exceptions and GPU driver crashes when concurrent browser/OS tasks run.
2. **Use `base` or `small` with `compute_type="int8"`.** Int8 quantization in CTranslate2 cuts memory requirements in half while preserving speech accuracy.
3. **Hardware Governor Enforced:** GPU inference is protected by `HardwareGovernor.gpu_bound_slot()` which enforces a strict concurrency ceiling of `GPU_MAX_CONCURRENT_INFERENCE = 1`.

---

## 3. Installation Instructions

### To Enable `faster-whisper` (Local CTranslate2):
```bash
uv pip install faster-whisper
```

### To Enable `whisper.cpp` (C++ Compilation):
```bash
# Clone and build
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
# Download base model
bash ./models/download-ggml-model.sh base
# Link to PATH
export PATH="$PATH:$(pwd)"
```

### Sovereign Cloud Policy:
Cloud transcription is strictly opt-in and disabled by default. It requires:
1. `settings.CLOUD_PROCESSING_ENABLED = True`
2. Setting an API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`)
3. Explicit user consent parameter `user_consent=True` in the analysis request payload.
