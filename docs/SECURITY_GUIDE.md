# DocuMind AI — Security Architecture & Hardening Guide

## 1. Zero-Trust Ingestion Architecture

DocuMind AI processes untrusted files from external users across dozens of file formats. The platform enforces strict zero-trust boundaries at every step of file ingestion and processing:

```
[Untrusted File Upload]
         │
         ▼
[Magic Number & MIME Detection] ──► [Block disallowed executable/binary payloads]
         │
         ▼
[File Size & Resource Gating]   ──► [Enforce per-format max byte limits]
         │
         ▼
[Safe Sandbox / Isolation]      ──► [Parser-level sandboxes, defused parsers]
         │
         ▼
[Canonical Document Model]      ──► [Standardized, sanitized representation]
```

---

## 2. Ingestion Defenses by File Modality

### A. Document & PDF Defenses
- **JavaScript & Embedded Script Execution:** Stripped completely during parsing. PDF objects containing `/JS` or `/JavaScript` actions are ignored and sanitized.
- **Embedded Binary Attachments:** Embedded EXE/ELF binaries inside PDFs or Office Open XML containers are blocked and quarantined.
- **Formula Injection (DDE) in CSV/Excel:** Any cell starting with `=, +, -, @` is sanitized with leading quotes or escaped to neutralize Dynamic Data Exchange (DDE) exploits.

### B. Image & Visual Defenses
- **Decompression Bombs (Pixel Floods):** Pillow `Image.MAX_IMAGE_PIXELS` set to bounded threshold (178,956,970 pixels); images exceeding dimensional limits raise `DecompressionBombError` immediately before allocation.
- **EXIF Stripping:** GPS latitude/longitude, camera serial numbers, and sensitive EXIF tags are stripped during preprocessing to protect user privacy.

### C. Archive & Container Defenses
- **Zip Slip (Path Traversal):** Filenames containing `..`, leading slashes (`/` or `\`), or absolute drive letters are normalized and validated to ensure extraction targets never escape the sandbox root directory.
- **Zip Bomb (Decompression Amplification):** Cumulative uncompressed size is tracked per archive. Ratios exceeding 100:1 or total expanded size > 1 GB trigger instant extraction abortion.
- **Symlink Attacks:** Symbolic and hard links targeting files outside the archive root are refused.

### D. Code & Structured Data Defenses
- **XML External Entity (XXE):** XML parsing utilizes `defusedxml` with entity expansion and external DTD resolution completely disabled.
- **YAML Alias Bombs (Billion Laughs):** PyYAML uses `yaml.SafeLoader` with strict recursion limits to prevent memory exhaustion from recursive alias expansions.
- **Arbitrary Code Execution:** Python `pickle.loads` is strictly forbidden across all ingestion and serialization pipelines.

---

## 3. AI Trustworthiness & Prompt Injection Defenses

### A. Grounded Fact Verification
The Sovereign LLM engine (`sovereign_llm_provider`) operates under a strict deterministic grounding policy:
- **Strict Evidence Requirement:** Statements must be backed by retrieved content chunks.
- **Citation Precision:** Every synthesized claim references source file UUID, original filename, page/sheet/slide number, and timestamp.
- **Explicit Abstention:** If contextual evidence is insufficient or missing, the model returns an explicit disclaimer rather than hallucinating details.

### B. Prompt Injection Neutralization
User prompts undergo input sanitization prior to inference:
- Patterns matching `ignore previous instructions`, `bypass safety rules`, `you are now DAN`, etc., are scrubbed and replaced with safety notices.
- System instructions are strictly isolated from user document context blocks to prevent delimiter hijacking.

---

## 4. Authentication, Authorization & Tenant Isolation

- **Token Security:** JWT tokens signed using HMAC-SHA256 with strong secrets (`SECRET_KEY` >= 32 bytes).
- **Password Hashing:** Passwords hashed with bcrypt (work factor 12).
- **Tenant Isolation:** All file, job, and knowledge records are scoped to `owner_id`. Queries strictly filter by user ID, preventing cross-tenant information leakage.
- **Cascading Deletion:** Deleting a file cascades deletion to database records, physical filesystem files, extracted artifacts, and keyframes.

---

## 5. Network & HTTP Hardening

The application applies comprehensive HTTP security headers via middleware:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` (in production mode)
