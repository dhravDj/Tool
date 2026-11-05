# DocuMind AI — OCR Engine Configuration & Deployment Guide

**Engine:** Tesseract OCR (with multi-engine adapter architecture)  
**Python Interface:** `pytesseract` / asynchronous worker wrapper  

---

## 1. Overview & Architecture

DocuMind AI uses a decoupled OCR routing architecture:
- In **document processing** (Phase 3), the `OCRRouter` evaluates digital text density against `OCR_DENSITY_THRESHOLD_CHARS` (default: 40 characters) and routes low-density or scanned pages to OCR.
- In **image processing** (Phase 4), the `ImageOCREngine` analyzes high-contrast binarized working images, isolating word- and line-level bounding boxes and reconstructing reading order.

---

## 2. Installation & Host Environment Setup

### 2.1 Ubuntu / Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

To install additional language packs:
```bash
# Spanish, German, French, Chinese, Japanese
sudo apt-get install -y tesseract-ocr-spa tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-chi-sim tesseract-ocr-jpn
```

### 2.2 macOS (Homebrew)
```bash
brew install tesseract
brew install tesseract-lang
```

### 2.3 Docker Deployment (Recommended)
The DocuMind production runtime image (`infrastructure/docker/Dockerfile.backend`) installs Tesseract automatically:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*
```

---

## 3. Configuration Parameters

Environment variables configured in `.env` or application settings (`app/core/config.py`):

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `OCR_ENABLED` | bool | `true` | Master flag enabling or disabling OCR routing across the platform. |
| `OCR_DENSITY_THRESHOLD_CHARS` | int | `40` | Minimum character threshold per PDF page before routing to OCR. |
| `OCR_ENGINE` | str | `"tesseract"` | Active OCR adapter identifier. |

---

## 4. Diagnostics & Capabilities Verification

DocuMind AI provides dedicated API endpoints and startup logging to verify OCR engine readiness:

### 4.1 CLI / API Diagnostics
```http
GET /api/v1/image-intelligence/capabilities
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "supported_formats": ["png", "jpeg", "webp", "tiff", "bmp", "svg"],
    "ocr_engine": "tesseract",
    "ocr_available": true,
    "default_vision_engine": "documind-vision-lite",
    "hardware_acceleration": "cpu",
    "privacy_gps_scrubbing": true
  }
}
```

### 4.2 Graceful Fallback Behavior
When Tesseract is not installed on the host machine:
1. The platform **does not crash** or throw 500 errors.
2. The pipeline logs a diagnostic warning:  
   `"OCR engine (Tesseract) is unavailable on this host; text extraction was skipped."`
3. Document extraction and image intelligence pipelines continue, capturing all visual metadata, scene captions, dominant colors, diagram structures, and chart data.
