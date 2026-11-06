# Universal AI Intelligence Schema & Storage Specification (Phase 11)

## 1. Domain Schemas

### `SourceReference`
Represents the exact physical or logical location of extracted content within its source asset.
- `source_file_id` (str): Unique UUID of the source `FileRecord`.
- `original_filename` (str): Basename of the file (e.g. `financial_report.pdf`).
- `source_type` (str): Ingested modality (`document`, `image`, `spreadsheet`, `presentation`, `audio`, `video`, `code`, `structured_data`, `archive`).
- `formatted_citation` (str): Human-readable locator (e.g. `report.pdf — Page 12`, `sheet.xlsx — Sheet: Revenue, Cells B2:F12`, `meeting.mp3 — 00:02:14–00:02:31`).
- `page_number` (int | null): 1-indexed document page number.
- `sheet_name` (str | null): Excel or ODS worksheet name.
- `cell_range` (str | null): Coordinate range (e.g. `A1:D20`).
- `slide_number` (int | null): 1-indexed presentation slide number.
- `timestamp_start` / `timestamp_end` (float | null): Audio/video seconds interval.
- `line_start` / `line_end` (int | null): 1-indexed source code lines.
- `json_path` (str | null): Structured JSON pointer (e.g. `$.database.credentials.host`).
- `archive_path` (str | null): Relative entry path inside an unpacked archive.

### `KnowledgeDocument`
Universal canonical envelope produced by modality adapters.
- `knowledge_document_id` (str): `kd_{type}_{file_id[:8]}`
- `source_file_id` (str): Source file UUID.
- `parent_archive_id` (str | null): If extracted from an archive, the parent archive UUID.
- `source_type` (str): Modality type.
- `content_type` (str): MIME type or format identifier.
- `title` (str): Title or original filename.
- `content_blocks` (list[ContentBlock]): Normalized semantic blocks.
- `content_hash` (str): SHA-256 hash of normalized text for idempotency.
- `created_at` (str): ISO 8601 creation timestamp.

---

## 2. Database Models (`backend/app/infrastructure/database/models.py`)

Implemented in migration `010_ai_intelligence_records.py`:

1. **`knowledge_documents` (`KnowledgeDocumentRecord`)**:
   - `id` (UUID, Primary Key)
   - `file_id` (UUID, ForeignKey `files.id` ON DELETE CASCADE)
   - `knowledge_document_id` (String 64, Index)
   - `source_type` (String 32, Index)
   - `content_type` (String 64)
   - `title` (String 255)
   - `content_hash` (String 64, Index)
   - `extraction_status` (String 32)
   - `language` (String 16)
   - `total_blocks` (Integer)
   - `total_tokens` (Integer)
   - `raw_metadata` (JSONB / JSON)
   - `created_at`, `updated_at` (DateTime TZ)

2. **`knowledge_chunks` (`KnowledgeChunkRecord`)**:
   - `id` (UUID, Primary Key)
   - `knowledge_document_id` (UUID, ForeignKey `knowledge_documents.id` ON DELETE CASCADE)
   - `file_id` (UUID, ForeignKey `files.id` ON DELETE CASCADE, Index)
   - `chunk_id` (String 128, Unique, Index)
   - `chunk_index` (Integer)
   - `content` (Text, NOT NULL)
   - `token_count` (Integer)
   - `source_type` (String 32, Index)
   - `source_reference` (JSONB / JSON, NOT NULL)
   - `content_hash` (String 64)
   - `embedding_status` (String 32)
   - `metadata_payload` (JSONB / JSON)

3. **`embedding_records` (`EmbeddingRecord`)**:
   - `id` (UUID, Primary Key)
   - `chunk_id` (UUID, ForeignKey `knowledge_chunks.id` ON DELETE CASCADE, Index)
   - `provider` (String 64)
   - `model_name` (String 128)
   - `dimension` (Integer)
   - `vector_data` (JSON / ARRAY)
   - `content_hash` (String 64)
   - `created_at` (DateTime TZ)

4. **`ai_conversations` (`AIConversationRecord`)**:
   - `id` (UUID, Primary Key)
   - `user_id` (UUID | null, ForeignKey `users.id`)
   - `file_id` (UUID | null, ForeignKey `files.id`)
   - `title` (String 255)
   - `provider` (String 64)
   - `model_name` (String 128)
   - `context_mode` (String 32: `single_file`, `multi_file`, `workspace`)
   - `created_at`, `updated_at` (DateTime TZ)

5. **`ai_messages` (`AIMessageRecord`)**:
   - `id` (UUID, Primary Key)
   - `conversation_id` (UUID, ForeignKey `ai_conversations.id` ON DELETE CASCADE)
   - `role` (String 16: `user`, `assistant`, `system`)
   - `content` (Text)
   - `citations` (JSONB / JSON)
   - `tokens_used` (Integer)
   - `latency_ms` (Float)
   - `created_at` (DateTime TZ)

6. **`retrieval_records` (`RetrievalRecord`)**:
   - Logs query, retrieval mode (`keyword`, `semantic`, `hybrid`), hit count, latency, and top retrieved chunk IDs for observability and relevance tuning.

7. **`ai_provider_configs` (`AIProviderConfigRecord`)**:
   - Stores per-user or platform provider credentials (encrypted), default model preferences, local daemon URLs, and cloud consent flags.

8. **`ai_usage_records` (`AIUsageRecord`)**:
   - Tracks operational token consumption, embedding count, inference latency, and estimated cloud provider costs.

9. **`summary_records` (`SummaryRecord`)**:
   - Caches pre-computed summaries across styles (`short`, `detailed`, `executive`, `bullet`, `technical`, `section_wise`, `key_findings`) with content hash invalidation.
