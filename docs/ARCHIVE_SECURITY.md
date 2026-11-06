# DocuMind AI — Archive Security & Threat Defense Architecture

## 1. Overview

Archive processing represents one of the most critical attack surfaces in document and file ingestion pipelines. Attackers routinely weaponize archives through directory traversal exploits, algorithmic compression bombs, symlink escapes, and malicious payload smuggling.

The Archive Intelligence Engine implements multi-layered defensive controls to guarantee safe execution and container isolation.

---

## 2. Threat Vector Defenses

### 1. Directory Traversal Defense (Zip Slip)
- **Attack Vector:** Archives containing paths with `../`, absolute paths (`/etc/shadow`), or Windows drive letters (`C:\Windows\system.ini`) intended to overwrite system binaries or configuration files outside the staging folder.
- **Defensive Mechanism:**
  - `PathSecurityValidator.sanitize_and_normalize` parses each entry path before extraction.
  - Slashes are converted to POSIX `/`.
  - Leading `/` or `\` triggers immediate `PathTraversalError`.
  - Windows drive patterns (`^[a-zA-Z]:`) trigger immediate `PathTraversalError`.
  - UNC network paths (`^[/\\]{2}`) trigger immediate `PathTraversalError`.
  - Null bytes (`\0`) trigger immediate rejection.
  - Path components are split and strictly evaluated: any `..` component triggers immediate `PathTraversalError`.
  - Strict filesystem containment verification: `resolved_dest.is_relative_to(dest_root)` is enforced prior to creating files or directories on disk.

### 2. Archive Bomb & Resource Exhaustion Defense
- **Attack Vector:** Tiny compressed files that expand to petabytes of data (e.g., recursive 42.zip or single-layer massive zero-byte streams), crashing workers via Out-of-Memory (OOM) or filling local disk volumes.
- **Defensive Mechanism:**
  - **Inspection-time ratio validation:** If reported uncompressed size divided by compressed size exceeds `max_compression_ratio` (default `100.0`), the archive is flagged as a bomb suspect.
  - **Runtime streaming accounting:** `ExtractionQuotaTracker` measures actual uncompressed bytes written in real-time chunk-by-chunk. If the runtime ratio exceeds the safety limit, decompression is halted immediately.
  - **Single file size limit:** Hard ceiling of 1 GB per extracted file (`max_single_file_size_bytes`).
  - **Total extracted volume limit:** Hard ceiling of 5 GB cumulative extracted data per job (`max_total_extracted_size_bytes`).
  - **Entry count cap:** Maximum of 10,000 entries per archive.
  - **Execution timeout:** Maximum of 300 seconds per archive job.

### 3. Symlink & Hardlink Escape Defense
- **Attack Vector:** Archive members containing symlinks pointing to sensitive host locations (e.g. `/etc`, `/proc`, `/sys`, `/dev`, or `..`) or hardlinks targeting files outside the extraction tree.
- **Defensive Mechanism:**
  - Symlinks are inspected in-place without following targets.
  - Symlinks pointing to paths outside the extraction staging directory are rejected and blocked.
  - Symlinks targeting system paths (`/etc`, `/proc`, `/sys`, `/dev`, `/root`) are blocked.
  - Hardlinks targeting files outside the destination root are rejected.

### 4. Special Device Nodes & Inode Poisoning
- **Attack Vector:** TAR or CPIO archives attempting to instantiate character devices, block devices, named pipes (FIFOs), or Unix domain sockets.
- **Defensive Mechanism:**
  - Member types are inspected: character devices (`chr`), block devices (`blk`), FIFOs (`fifo`), and sockets are explicitly blocked and quarantined.
  - Only regular files and standard directories are unpacked.

### 5. Recursive Nesting & Zip-in-Zip Cycles
- **Attack Vector:** Infinitely nested archives or circular archives designed to cause stack overflow or infinite extraction loops.
- **Defensive Mechanism:**
  - Hard recursion depth limit: Max 5 levels of nested archives (`max_nesting_depth`).
  - SHA256 cycle detection: The pipeline maintains a visited set of archive SHA256 hashes. If an extracted child archive hash matches any ancestor archive in the chain, extraction terminates with a cycle warning.

### 6. Sandboxing & Safe Handling
- **No Unsafe Execution:** No unpacked scripts (`.sh`, `.bat`, `.ps1`), binaries (`.exe`, `.elf`), or code files are ever executed directly by the worker. They are purely read as static byte streams for static intelligence analysis.
- **Temporary Staging Isolation:** Extractions occur in isolated temporary workspaces with restrictive directory permissions (`0o700`).
