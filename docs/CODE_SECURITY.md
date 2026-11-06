# DocuMind AI — Code & Structured Data Security Architecture

## 1. Principles of Static Isolation

DocuMind AI guarantees that analyzing user-uploaded code or structured data does **never execute code or jeopardize host integrity**:

1. **No Dynamic Invocation (`eval`, `exec`):**
   - Code is analyzed strictly via abstract syntax trees (Python standard library `ast`) or robust external tokenizers/parsers (`sqlglot`).
   - Compilers (`gcc`, `clang`, `rustc`, `javac`) and runtimes (`node`, `python`, `php`) are never invoked on user code.
2. **Defensive XML Entity Protection (XXE):**
   - All XML parsing is wrapped with `defusedxml.ElementTree.fromstring`.
   - External entity resolution, parameter entities, and DTD network fetching are explicitly forbidden, neutralizing SSRF and local file disclosure attacks (`file:///etc/passwd`).
3. **YAML Billion Laughs & Expansion Bomb Defense:**
   - Unsafe YAML loading (`yaml.load`) is banned; only `yaml.safe_load` is permitted.
   - Anchor (`&anchor`) and alias (`*alias`) densities are audited. Excessive alias counts (> 25 with recursive anchors) are flagged and bounded to prevent gigabyte-scale memory exhaustion.
4. **JSON Duplicate Key Trapping:**
   - Standard JSON parsers discard duplicate keys silently, hiding tampering or misconfigurations.
   - An `object_pairs_hook` audits duplicate keys before dictionary construction and records duplicate key warnings.
5. **Bounded Zero-Dataframe Parquet Streaming:**
   - Parquet metadata and schemas are inspected from binary footers without loading full tables.
   - Sample records are retrieved using bounded streaming iterator batches of at most 50 rows.
