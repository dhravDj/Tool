# DocuMind AI — Privacy, Data Retention & Compliance Guide

## 1. Data Classification & Inventory

DocuMind AI stores and processes the following data categories:

| Data Category | Storage Location | Sensitivity | Retention Policy | Cascading Deletion |
|---|---|---|---|---|
| **Raw Uploaded Files** | Local filesystem (`./storage/uploads`) / Cloud Bucket | High (User PII / Intellectual Property) | Configurable (Default: Indefinite until deleted) | Hard unlink on file deletion |
| **Extracted Text & Blocks** | PostgreSQL (`extraction_records`) | High | Matches raw file lifecycle | Cascades with `file_id` deletion |
| **Vector Embeddings** | PostgreSQL (`embedding_records`) | Medium (Derived mathematical vectors) | Matches raw file lifecycle | Cascades with `file_id` deletion |
| **AI Knowledge Chunks** | PostgreSQL (`knowledge_chunk_records`) | High | Matches raw file lifecycle | Cascades with `file_id` deletion |
| **Media Derivatives** | Local filesystem (`./storage/keyframes`, `./storage/extracted`) | Medium | Matches raw file lifecycle | Directory tree deleted recursively |
| **Application Audit Logs** | Application log streams (`stdout`) | Low | 90 days log rotation | Retained by log collector |

---

## 2. Hardened Cascading File Deletion

To comply with GDPR "Right to be Forgotten" and enterprise zero-footprint requirements, deleting a file via `DELETE /api/v1/files/{file_id}` executes a cryptographically clean, cascading purge:

1. **Physical Filesystem Unlink:**
   - Raw uploaded original file is unlinked from `./storage/uploads/{file_id}_{filename}`.
   - Extracted child files directory (`./storage/extracted/{file_id}/`) is recursively deleted.
   - Video keyframes directory (`./storage/keyframes/{file_id}/`) is recursively deleted.

2. **Relational Database Purge:**
   - Deletion of records in proper dependency order across all 13 phases:
     - `EmbeddingRecord`
     - `KnowledgeChunkRecord`
     - `KnowledgeDocumentRecord`
     - `SummaryRecord`
     - `ArchiveRelationshipRecord`
     - `ArchiveEntryRecord`
     - `ArchiveAnalysisRecord`
     - `StructuredDataAnalysisRecord`
     - `CodeAnalysisRecord`
     - `VideoAnalysisRecord`
     - `AudioAnalysisRecord`
     - `PresentationAnalysisRecord`
     - `SpreadsheetAnalysisRecord`
     - `ImageAnalysisRecord`
     - `ExtractionRecord`
     - `ProcessingJobRecord`
     - `BatchFileRecord`
     - `FileRecord`

---

## 3. Privacy-First Image & Document Processing

- **Automatic EXIF Sanitization:** Sensitive image metadata (GPS coordinates, camera serial numbers, creation timestamps, lens details) is stripped during ingestion before storing visual records.
- **Formula Injection Neutralization:** Spreadsheets containing CSV formulas starting with `=,+,-,@` are escaped with leading single quotes to prevent client-side credential exfiltration when exported.

---

## 4. External AI Model Policy & Data Sovereignty

- **Sovereign Local Mode (Default):**
  - Uses `sovereign_llm_provider` and `fast_local_embedder`.
  - Zero external HTTP calls; zero data transmission outside the platform perimeter.
  - Recommended for air-gapped, defense, healthcare, and enterprise confidential workflows.

- **External Cloud AI (Optional - Gemini / OpenAI):**
  - Requires explicit opt-in via environment configuration (`GEMINI_API_KEY`).
  - Strict zero data retention (ZDR): Google Cloud Vertex AI and Gemini API terms certify that customer data is not used to train foundation models.
  - Transparent user disclaimer surfaced in the UI whenever an external provider is selected.
