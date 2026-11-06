# DocuMind AI — Phase 9 Performance & Resource Report
## Code & Structured Data Intelligence Engine

**Evaluation Date:** 2026-11-06  
**Benchmarking Environment:** Linux x86_64, Python 3.13.15, Tracemalloc profiler  
**Tool:** `scripts/evaluate_phase_9.py`

---

## 1. Executive Summary

Phase 9 was designed with strict memory bounding and sub-10ms parsing targets:
- **Code Parsing Average Latency:** **4.59 ms** across 15 test files in 14 programming languages.
- **Code Peak Memory Usage:** **24.5 KB – 207.4 KB** per file (no compiler invocations, AST + static scanner).
- **Structured Data Average Latency:** **46.66 ms** across 11 files (including recursive alias bomb inspection).
- **Zero-Dataframe Parquet Inspection:** **3.40 ms** latency, **148.5 KB** peak memory (metadata read + bounded 50-row batch iteration).
- **Graceful Error Trapping:** Broken files isolated in **< 2.0 ms** without server heap disruption.

---

## 2. Empirical Benchmark Data

### 2.1 Code Intelligence Engine (14 Languages)

| Language | Test File | Line Count | Symbols | Diagnostics | Status | Latency (ms) | Peak Heap (KB) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **C** | `sample_c.c` | 22 | 3 | 1 | VALID | 6.99 ms | 59.7 KB |
| **C++** | `sample_cpp.cpp` | 24 | 2 | 0 | VALID | 3.13 ms | 31.5 KB |
| **Go** | `sample_go.go` | 24 | 3 | 0 | VALID | 5.37 ms | 33.6 KB |
| **Java** | `sample_java.java` | 25 | 2 | 0 | VALID | 5.90 ms | 40.5 KB |
| **JavaScript** | `sample_javascript.js` | 24 | 2 | 1 | VALID | 8.57 ms | 156.6 KB |
| **HTML** | `sample_page.html` | 26 | 4 | 1 | VALID | 2.89 ms | 36.3 KB |
| **PHP** | `sample_php.php` | 18 | 3 | 0 | VALID | 4.08 ms | 31.7 KB |
| **Python** | `sample_python.py` | 32 | 4 | 4 | VALID | 7.21 ms | 207.4 KB |
| **Python (Broken)** | `sample_python_syntax_error.py` | 2 | 0 | 1 | SYNTAX_ERROR | 1.87 ms | 45.9 KB |
| **React JSX** | `sample_react.jsx` | 18 | 2 | 0 | VALID | 2.29 ms | 24.8 KB |
| **React TSX** | `sample_react.tsx` | 17 | 2 | 0 | VALID | 2.63 ms | 24.5 KB |
| **Rust** | `sample_rust.rs` | 20 | 4 | 1 | VALID | 3.78 ms | 37.2 KB |
| **SQL** | `sample_schema.sql` | 19 | 2 | 0 | VALID | 8.50 ms | 193.2 KB |
| **CSS** | `sample_styles.css` | 28 | 6 | 0 | VALID | 2.88 ms | 32.5 KB |
| **TypeScript** | `sample_typescript.ts` | 28 | 4 | 0 | VALID | 2.79 ms | 32.5 KB |

**Summary Statistics:**
- **Average Latency:** 4.59 ms
- **Median Latency:** 3.13 ms
- **P95 Latency:** 8.54 ms
- **Max Memory:** 207.4 KB (`sample_python.py` AST parsing + docstring analysis)
- **Min Memory:** 24.5 KB (`sample_react.tsx`)
- **Throughput Capability:** ~218 files/second per CPU core

---

### 2.2 Structured Data Intelligence Engine (5 Formats)

| Format | Test File | Rows | Columns | Security / Dup Alerts | Status | Latency (ms) | Peak Heap (KB) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **YAML (Bomb)** | `alias_bomb.yaml` | 6 | 6 | 1 Alert | VALID | 490.82 ms | 13,433.1 KB |
| **Parquet (Corrupt)**| `corrupted.parquet` | 0 | 0 | 0 Alerts | INVALID/BLOCKED | 1.82 ms | 15.8 KB |
| **JSON (Dup Keys)** | `duplicate_keys.json`| 1 | 3 | 2 Dup Keys | VALID | 1.88 ms | 143.9 KB |
| **JSON (Malformed)**| `invalid.json` | 0 | 0 | 0 Alerts | INVALID/BLOCKED | 1.26 ms | 13.7 KB |
| **JSON (Deep Nested)**| `nested.json` | 1 | 1 | 0 Alerts | VALID | 1.77 ms | 141.7 KB |
| **JSON (Valid)** | `valid.json` | 1 | 5 | 0 Alerts | VALID | 1.82 ms | 151.2 KB |
| **Parquet (Valid)** | `valid.parquet` | 5 | 4 | 0 Alerts | VALID | 3.40 ms | 148.5 KB |
| **TOML (Valid)** | `valid.toml` | 3 | 3 | 0 Alerts | VALID | 3.55 ms | 20.3 KB |
| **XML (Valid)** | `valid.xml` | 15 | 8 | 0 Alerts | VALID | 2.14 ms | 154.8 KB |
| **YAML (Valid)** | `valid.yaml` | 2 | 2 | 0 Alerts | VALID | 3.55 ms | 142.8 KB |
| **XML (XXE Attack)**| `xxe_attack.xml` | 0 | 0 | 1 Alert | INVALID/BLOCKED | 1.27 ms | 25.4 KB |

**Summary Statistics:**
- **Average Latency (Clean Files):** 2.45 ms
- **Parquet Profiling Latency:** 3.40 ms
- **Parquet Peak Memory:** 148.5 KB
- **Security Interception Latency:** 1.27 ms (XXE), 1.82 ms (Corrupted Parquet)
- **Alias Expansion Defense:** 13.4 MB bounded heap limit (preventing GB-scale server OOM)

---

## 3. Architecture & Optimization Highlights

1. **Zero Dynamic Execution:**
   - No `eval()`, `exec()`, `node`, `gcc`, or external compiler processes are invoked.
   - All parsing occurs through deterministic static parsers (`ast`, `sqlglot`, `defusedxml`, `tomllib`, `yaml.safe_load`).
2. **Zero-Dataframe Parquet Streaming:**
   - `pyarrow.parquet.ParquetFile` inspects file metadata directly for row counts, schema, and column statistics.
   - Bounded record batches (`iter_batches(batch_size=50)`) extract sample data without creating a full pandas/arrow table in memory.
3. **Defense-in-Depth:**
   - XML parsing forbids external DTDs (`defusedxml.ElementTree.fromstring`), blocking SSRF and file disclosure.
   - YAML anchor and alias frequencies are audited before traversal to neutralize Billion Laughs attacks.
   - JSON parsing captures duplicate keys with `object_pairs_hook` before dict overwrite.
