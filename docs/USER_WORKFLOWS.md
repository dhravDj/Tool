# DocuMind AI — User Workflows Guide (Phase 13)

This guide documents the complete end-to-end user workflows supported by the unified DocuMind AI platform.

---

## Workflow A: Single File Upload & Instant Inspection

1. Navigate to `/upload` using the sidebar or press `Ctrl+K` and type `Upload`.
2. Drag and drop any supported file into the central upload area or click **Browse Files**.
3. The zero-trust multi-signal detection pipeline evaluates magic numbers, MIME types, structure, and container headers.
4. Review the detection badge, confidence score, and format classification.
5. Click **Open Inspector** to launch the Universal File Inspector modal or full page, allowing immediate review of extracted text, tables, audio waveforms, or code ASTs.

---

## Workflow B: Folder / Multi-File Ingestion & Deduplication

1. On `/upload`, click **Select Directory** to choose an entire folder containing heterogeneous file types.
2. The platform queues each file, streaming requests to the server.
3. Pre-upload deduplication checks verify each file's SHA-256 hash against existing records:
   - Unique files are persisted to the library.
   - Exact duplicate files trigger an inline warning badge with the existing file's name and skip redundant processing.
4. Each ingested file displays a recommended next action tailored to its specific format (e.g. *Extract Slides & Diagrams* for `.pptx`, *Transcribe Speech* for `.wav`).

---

## Workflow C: Universal Inspection Across Formats

The Universal File Inspector (`/inspector/:fileId`) adapts dynamically to any format category:

- **Documents (PDF, DOCX, TXT, MD, HTML)**: Page-by-page text extraction, structural hierarchy, embedded tables, and visual bounding boxes.
- **Spreadsheets (XLSX, XLS, CSV, TSV)**: Sheet tabs, cell formulas, grid previews, column statistics, and anomaly highlights.
- **Presentations (PPTX, ODP)**: Slide thumbnails, presentation layout structure, speaker notes, and shape extractions.
- **Images (JPEG, PNG, WEBP, TIFF)**: High-resolution preview, OCR text detection bounding boxes, color palette, and EXIF camera metadata.
- **Audio (MP3, WAV, M4A, FLAC)**: Interactive waveform visualization, speaker diarization segments, and synchronized transcription tracks.
- **Video (MP4, MKV, AVI, MOV)**: Keyframe gallery, timeline navigation, scene changes, and audio transcript alignment.
- **Code (Python, JS, TS, Go, Rust, C)**: Syntax-highlighted code viewer, AST symbol outline (functions, classes), and cyclomatic complexity score.
- **Structured Data (JSON, XML, YAML, Parquet)**: Interactive collapsible tree view, schema validation report, and tabular data view.
- **Archives (ZIP, TAR, 7Z, GZ)**: Interactive directory tree viewer, nested file extraction, compression ratio, and zip-bomb safety alerts.

---

## Workflow D: File Library Management

1. Access `/files` from the sidebar navigation.
2. Switch between **Table View** (dense metadata, sorting, direct actions) and **Grid View** (visual cards with format badges).
3. Filter files by category (*Documents, Spreadsheets, Presentations, Audio, Video, Code, Structured Data, Archives*) or status (*Processed, Processing, Error*).
4. Search file names or format IDs via the real-time debounced search bar.
5. Click **Download** to retrieve the original binary payload.
6. Click **Delete** to open the accessible confirmation dialog and safely remove the record and storage assets.

---

## Workflow E: Cross-Format Hybrid Search

1. Navigate to `/search` or press `Ctrl+K` -> `Knowledge Search`.
2. Enter a natural language query (e.g. *"Q3 revenue growth and audio transcript commentary"*).
3. The backend executes Reciprocal Rank Fusion combining BM25 keyword search with dense vector embeddings.
4. Review matching chunks, confidence scores, and source file citations with clickable deep links directly into the file inspector.

---

## Workflow F: Conversational AI Workspace

1. Navigate to `/ai` to launch the multi-turn conversational RAG workspace.
2. Select your preferred LLM provider and model via the Model Selector.
3. Choose knowledge grounding scope: **All Library Files** or **Selected Document Focus**.
4. Ask analytical questions; receive streamed answers containing exact bracketed citations linking back to original file chunks.

---

## Workflow G: Bulk Pipeline Execution

1. Navigate to `/bulk-processing`.
2. Create a new processing batch container with custom concurrency and processing policies.
3. Upload batches of up to 1,000+ files.
4. Monitor execution velocity, batch progress bars, pause and resume processing mid-run, and trigger one-click retries for transiently failed items.

---

## Workflow H: Task Queue Monitoring & Job Diagnostics

1. Navigate to `/jobs`.
2. Inspect live queue depths across high, normal, bulk, and dead-letter queues.
3. Filter tasks by execution stage (`detect`, `extract`, `analyze`, `index`).
4. View detailed attempt histories, execution durations, worker IDs, and stack traces for failed jobs.
5. Cancel running tasks or trigger immediate retries.

---

## Workflow I: Hardware & Concurrency Configuration

1. Navigate to `/settings` and select the **Hardware & Concurrency** tab.
2. Review real-time CPU and GPU slot utilization and backpressure status.
3. Adjust worker concurrency sliders (CPU bound, I/O bound, GPU bound) according to server hardware profiles.
4. Save configuration with instant toast confirmation.

---

## Workflow J: Global Keyboard Navigation & Command Palette

1. Press `Ctrl+K` (or `Cmd+K` on macOS) anywhere within the application.
2. Type to search across routes, actions, and stored documents.
3. Use `ArrowUp` and `ArrowDown` to navigate results, and `Enter` to jump instantly.
4. Press `Escape` to close the palette.
