"""DocuMind AI — Document Extraction Engine Performance Benchmark."""

import asyncio
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import time
import zipfile

import docx
from ebooklib import epub
import pymupdf

from app.modules.extraction.pipeline import extraction_pipeline
from tests.unit.test_extraction_adapters import create_synthetic_doc_bytes


def create_sample_files(temp_dir: Path) -> dict[str, Path]:
    """Generate representative sample files for each format."""
    files: dict[str, Path] = {}

    # 1. PDF
    pdf_path = temp_dir / "bench.pdf"
    doc = pymupdf.open()
    for p_idx in range(5):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 50), f"Benchmark Document Page {p_idx + 1}", fontsize=14)
        for i in range(15):
            p.insert_text(
                (50, 90 + i * 25),
                f"Paragraph line {i+1}: Performance profiling of native text extraction with coordinates.",
                fontsize=10,
            )
    doc.save(str(pdf_path))
    doc.close()
    files["pdf"] = pdf_path

    # 2. DOCX
    docx_path = temp_dir / "bench.docx"
    d = docx.Document()
    d.add_heading("Benchmark DOCX", level=1)
    for i in range(25):
        d.add_paragraph(f"Sample body paragraph {i+1} testing extraction throughput.")
    t = d.add_table(rows=5, cols=3)
    for r in range(5):
        for c in range(3):
            t.cell(r, c).text = f"Cell {r},{c}"
    d.save(str(docx_path))
    files["docx"] = docx_path

    # 3. DOC
    doc_path = temp_dir / "bench.doc"
    raw_doc = create_synthetic_doc_bytes("Legacy Word 97-2003 binary stream benchmark content.\n\n")
    doc_path.write_bytes(raw_doc)
    files["doc"] = doc_path

    # 4. TXT
    txt_path = temp_dir / "bench.txt"
    txt_content = "\n\n".join(
        f"Paragraph {i+1}: High-performance plain text decoding with encoding auto-detection."
        for i in range(50)
    )
    txt_path.write_text(txt_content, encoding="utf-8")
    files["txt"] = txt_path

    # 5. MD
    md_path = temp_dir / "bench.md"
    md_content = """# Markdown Extraction Benchmark

This is a comprehensive markdown document.

## Code Sample

```python
for i in range(100):
    print(f"Extraction benchmark {i}")
```

| Key | Value | Metric |
| --- | --- | --- |
| Latency | < 50ms | Success |
| Accuracy | 100% | Verified |
"""
    md_path.write_text(md_content, encoding="utf-8")
    files["md"] = md_path

    # 6. RTF
    rtf_path = temp_dir / "bench.rtf"
    rtf_path.write_bytes(
        b"{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Arial;}}\\f0\\fs24 Benchmark RTF Title\\par\\par "
        b"This is a rich text paragraph testing RTF extraction speed.\\par}"
    )
    files["rtf"] = rtf_path

    # 7. ODT
    odt_path = temp_dir / "bench.odt"
    content_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                         xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body><office:text>
    <text:h text:outline-level="1">ODT Benchmark</text:h>
    <text:p>Sample paragraph inside open document container.</text:p>
  </office:text></office:body>
</office:document-content>"""
    with zipfile.ZipFile(odt_path, "w") as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        zf.writestr("content.xml", content_xml)
    files["odt"] = odt_path

    # 8. EPUB
    epub_path = temp_dir / "bench.epub"
    book = epub.EpubBook()
    book.set_identifier("bench-1")
    book.set_title("Bench Book")
    c1 = epub.EpubHtml(title="Chapter 1", file_name="c1.xhtml")
    c1.content = "<h1>Chapter 1</h1><p>EPUB reading order performance evaluation.</p>"
    book.add_item(c1)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", c1]
    epub.write_epub(str(epub_path), book)
    files["epub"] = epub_path

    return files


async def run_benchmark(iterations: int = 10) -> dict[str, dict[str, float]]:
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        sample_files = create_sample_files(temp_dir)
        results: dict[str, dict[str, float]] = {}

        print("=" * 80)
        print(f" DOCUMIND AI — EXTRACTION ENGINE BENCHMARK ({iterations} iterations per format)")
        print("=" * 80)
        print(f"{'Format':<8} | {'Engine':<24} | {'Avg Latency':<12} | {'Min Latency':<12} | {'Throughput':<14}")
        print("-" * 80)

        for fmt, file_path in sample_files.items():
            extractor = extraction_pipeline.get_extractor(fmt)
            assert extractor is not None
            engine_name = extractor.engine_name

            latencies: list[float] = []

            # Warmup
            await extraction_pipeline.extract_path(file_path, fmt)

            for _ in range(iterations):
                t0 = time.perf_counter()
                await extraction_pipeline.extract_path(file_path, fmt)
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000)  # ms

            avg_lat = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            throughput = 1000.0 / avg_lat  # docs/sec

            results[fmt] = {
                "engine": engine_name,
                "avg_latency_ms": round(avg_lat, 2),
                "min_latency_ms": round(min_lat, 2),
                "throughput_docs_per_sec": round(throughput, 1),
            }

            print(
                f"{fmt:<8} | {engine_name:<24} | {avg_lat:8.2f} ms | {min_lat:8.2f} ms | {throughput:8.1f} docs/s"
            )

        print("=" * 80)
        return results


def main() -> None:
    res = asyncio.run(run_benchmark(iterations=10))
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "EXTRACTION_BENCHMARK.json"
    report_file.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "benchmark_results": res,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[+] Benchmark metrics persisted to {report_file}")


if __name__ == "__main__":
    main()
