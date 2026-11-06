# DocuMind AI — Archive Processing Quotas & Operational Limits

## 1. Overview

To protect production workers and infrastructure against Denial of Service (DoS) attacks and resource starvation, the Archive Intelligence Engine enforces strict resource limits and quotas.

Configuration Class: `ArchiveSafetyConfig` (`backend/app/modules/archive_intelligence/config.py`)

---

## 2. Default Quotas & Limits

| Setting | Default Value | Description | Enforcement Point |
|---|---|---|---|
| `max_archive_size_bytes` | 2 GB (`2,147,483,648` B) | Maximum allowed size of the input compressed archive file | Ingestion / Upload & Pipeline start |
| `max_single_file_size_bytes` | 1 GB (`1,073,741,824` B) | Maximum uncompressed size allowed for any single extracted member | Stream decompressed write loop |
| `max_total_extracted_size_bytes` | 5 GB (`5,368,709,120` B) | Maximum cumulative uncompressed bytes allowed across all extracted files | Cumulative quota tracker |
| `max_entries_per_archive` | 10,000 entries | Maximum number of files and directories permitted in a single archive | Header inspection & Member iterator |
| `max_total_entries_per_job` | 50,000 entries | Maximum total entries across parent and all recursively unpacked archives | Central pipeline tracker |
| `max_nesting_depth` | 5 levels | Maximum depth of recursive nested archive extraction | Recursion guard in pipeline |
| `max_compression_ratio` | 100.0:1 | Maximum uncompressed to compressed size ratio before flagging as bomb suspect | Inspection & Streaming extraction |
| `max_path_length` | 1,024 characters | Maximum character length for normalized relative member paths | Path security validator |
| `max_extraction_time_seconds` | 300 seconds (5 min) | Maximum execution wall-clock time permitted for processing an archive | Task runner & Extraction loop |
| `allow_symlinks` | `False` | Reject external symlinks by default | Symlink extraction validator |

---

## 3. Quota Exceeded Behavior

When any limit is reached:
- Decompression immediately stops to prevent further disk or memory consumption.
- Already extracted benign files remain accessible in the quarantine manifest.
- The corresponding safety flag (e.g. `size_limit_exceeded`, `compression_ratio_exceeded`) is marked `True` in `ArchiveSafetyReport`.
- A detailed explanation is recorded in `safety_report.warnings` and returned to the API caller.
- The archive status is set to `completed` with warnings, or `failed` if no files could be safely extracted.
