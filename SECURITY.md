# DocuMind AI — Security Foundation & Threat Mitigation

This document outlines the security architecture, threat model, input validation safeguards, and operational controls implemented for DocuMind AI.

---

## 1. Core Security Principles

1. **Zero Trust for Uploaded Files:** Never trust client-provided file names, extensions, or HTTP `Content-Type` headers.
2. **No Direct Execution:** Files uploaded to DocuMind AI are strictly treated as inert data streams. Under no circumstance are uploaded files executed or evaluated as code.
3. **Defense in Depth:** Validation occurs at multiple layers: network ingestion, storage abstraction, format detection, and engine isolation.
4. **Data Sovereignty by Default:** All AI inference and processing defaults to local execution. Cloud processing is explicitly disabled by default.

---

## 2. Threat Modeling & Safeguards

### 2.1 File Upload & Storage Safeguards

| Threat Vector | Risk | Mitigation in DocuMind AI |
|---|---|---|
| **Path Traversal (`../../etc/passwd`)** | Arbitrary file overwrite or system file leak | Uploaded filenames are sanitized: stripped of path separators (`/`, `\`), null bytes (`\0`), and path characters (`..`). Stored files are renamed using cryptographically secure UUIDv4 identifiers. |
| **Extension & MIME Spoofing** | Disguising malicious binaries as safe formats (e.g., `.exe` renamed to `.pdf`) | Multi-stage verification: Magic bytes / file signatures are checked first. Extension is strictly compared against registered MIME types. Mismatches trigger immediate rejection. |
| **Denial of Service via File Size** | Storage and memory exhaustion | Strict maximum upload limits enforced at API gateway level (default: 100 MB per file, configurable via `MAX_UPLOAD_SIZE_BYTES`). Streaming chunked writes prevent memory spikes. |
| **Archive / Decompression Bombs** | Zip bombs causing exponential disk/RAM exhaustion | Archive inspection checks total uncompressed size, compression ratios (>100:1 rejected), and nested depth (>3 levels rejected) before decompression. |
| **Malicious Polyglot Files** | Valid image and executable simultaneously | Files are ingested into sandboxed temporary storage with restrictive POSIX permissions (`0600` - read/write owner only, non-executable). |

---

## 2.2 API & Authentication Security

- **Authentication Architecture:** Modular design supporting API Keys (`X-API-Key`) and JWT Bearer Tokens (`Authorization: Bearer <token>`).
- **Password Storage:** Uses Argon2id or bcrypt with appropriate work factors for user credentials.
- **Authorization & Multi-Tenancy:** All file queries and job lookups are filtered by `owner_id`. No user can inspect or download files belonging to another tenant.
- **Rate Limiting:** IP and token-based rate limiting on sensitive endpoints (upload, batch creation, authentication) to prevent brute-force and resource starvation.
- **Error Sanitization:** Never leak internal stack traces, database column names, or local file system paths to the client. All exceptions are caught and mapped to standard API error responses with unique correlation IDs.

---

## 2.3 Cloud AI & Data Privacy Controls

- **Default Privacy Mode:** `CLOUD_PROCESSING_ENABLED=false` and `AI_MODE=local`.
- **Explicit Consent Guardrail:** In Phase 1 and future phases, no document text, embeddings, or file contents can be transmitted to external cloud APIs (e.g. Google Gemini, OpenAI, Anthropic) without:
  1. An explicit environment configuration enabling cloud processing.
  2. A verified API key configured by the administrator.
  3. Explicit job-level user consent flag (`allow_cloud_processing: true`).
- **Telemetry & Logging:** Document contents and extracted text are NEVER written to application logs. Only file hashes, job IDs, error codes, and performance metrics are logged.

---

## 2.4 Secure Temporary Storage & Lifecycle

- **Temporary Scratchpad:** Ephemeral files created during extraction are written to `storage/temporary/<job-id>/`.
- **Automatic Lifecycle Cleanup:** Workers use Python context managers (`try...finally`) and periodic garbage collector tasks to ensure temporary scratch directories are purged immediately upon job completion or failure.
- **Permanent File Deletion:** Deleting a file cascades to its stored binary on disk, its temporary records, and its associated extraction artifacts.

---

## 2.5 Secrets & Environment Management

- **Zero Hardcoded Secrets:** Passwords, API keys, database credentials, and cryptographic salts are injected exclusively via environment variables (`.env`).
- **`.gitignore` Enforcement:** `.env`, `*.pem`, `*.key`, storage directories (`storage/uploads/*`), and database files are strictly ignored by version control.
- **Example Template:** A safe `.env.example` file is provided with dummy placeholders and security guidance.
