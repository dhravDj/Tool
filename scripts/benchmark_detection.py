#!/usr/bin/env python3
"""DocuMind AI — Phase 2 Universal File Detection Engine Benchmark.

Profiles single-file latency, 100-file batch, and 1,000-file mixed-format batch.
Measures execution time, throughput (files/second), peak memory (MB), and accuracy.
"""

import io
import os
import shutil
import sys
import tempfile
import time
import tracemalloc
import zipfile
from pathlib import Path

# Ensure backend app is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.modules.files.detection.detector import universal_detector
from app.modules.formats.categories import FormatCategory


def create_specimen_generators():
    """Generators for valid test files across different categories."""

    def make_pdf():
        return b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Size 1 >>\nstartxref\n9\n%%EOF\n"

    def make_png():
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"

    def make_jpeg():
        return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"

    def make_docx():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            zf.writestr("word/document.xml", "<w:document/>")
        return buf.getvalue()

    def make_xlsx():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            zf.writestr("xl/workbook.xml", "<workbook/>")
        return buf.getvalue()

    def make_json():
        return b'{"project": "DocuMind AI", "phase": 2, "detection_ready": true, "records": [1, 2, 3]}'

    def make_python():
        return b"import sys\n\ndef main():\n    print('DocuMind benchmark')\n\nif __name__ == '__main__':\n    main()\n"

    def make_csv():
        return b"id,name,role,department\n1,Alice,Architect,Core\n2,Bob,Engineer,Core\n3,Carol,Security,Infra\n"

    def make_mismatch():
        # PDF named .jpg
        return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

    def make_unknown():
        return bytes([i % 256 for i in range(512)])

    return [
        ("pdf", "sample.pdf", make_pdf, "pdf"),
        ("png", "image.png", make_png, "png"),
        ("jpeg", "photo.jpg", make_jpeg, "jpeg"),
        ("docx", "doc.docx", make_docx, "docx"),
        ("xlsx", "sheet.xlsx", make_xlsx, "xlsx"),
        ("json", "config.json", make_json, "json"),
        ("python", "script.py", make_python, "py"),
        ("csv", "table.csv", make_csv, "csv"),
        ("mismatch", "fake.jpg", make_mismatch, "pdf"),
        ("binary", "data.bin", make_unknown, "binary"),
    ]


def run_single_file_benchmarks(temp_dir: Path):
    """Benchmark individual format detection latency."""
    print("=" * 70)
    print("1. SINGLE FILE DETECTION LATENCY (AVERAGED OVER 20 RUNS)")
    print("=" * 70)
    specimens = create_specimen_generators()
    results = []

    for name, filename, generator, expected_format in specimens:
        file_path = temp_dir / filename
        file_path.write_bytes(generator())

        durations = []
        for _ in range(20):
            t0 = time.perf_counter()
            res = universal_detector.detect_file(file_path, filename)
            durations.append((time.perf_counter() - t0) * 1000)

        avg_ms = sum(durations) / len(durations)
        min_ms = min(durations)
        max_ms = max(durations)
        correct = res.format_id == expected_format or (expected_format == "binary" and res.format_id in ("binary", "unknown"))

        results.append({
            "specimen": name,
            "filename": filename,
            "expected": expected_format,
            "detected": res.format_id,
            "avg_ms": avg_ms,
            "min_ms": min_ms,
            "max_ms": max_ms,
            "correct": correct,
        })
        print(f"  - {name:<12} ({filename:<12}): {avg_ms:6.3f} ms (min: {min_ms:6.3f} ms, max: {max_ms:6.3f} ms) | Match: {correct}")

    return results


def run_batch_benchmark(temp_dir: Path, count: int):
    """Benchmark large batch streaming detection."""
    print("\n" + "=" * 70)
    print(f"2. BATCH DETECTION PERFORMANCE ({count:,} FILES)")
    print("=" * 70)

    specimens = create_specimen_generators()
    batch_dir = temp_dir / f"batch_{count}"
    batch_dir.mkdir(exist_ok=True)

    # Populate batch files
    file_list = []
    for i in range(count):
        spec_type, fname, gen_func, expected_fid = specimens[i % len(specimens)]
        file_name = f"specimen_{i:04d}_{fname}"
        p = batch_dir / file_name
        p.write_bytes(gen_func())
        file_list.append((p, file_name, expected_fid))

    # Benchmark with memory tracking
    tracemalloc.start()
    start_time = time.perf_counter()

    correct_count = 0
    mismatch_detected_count = 0

    for path, name, expected_fid in file_list:
        res = universal_detector.detect_file(path, name)
        if res.format_id == expected_fid or (expected_fid == "binary" and res.format_id in ("binary", "unknown")):
            correct_count += 1
        if res.is_mismatch:
            mismatch_detected_count += 1

    total_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    throughput = count / total_time
    avg_per_file_ms = (total_time / count) * 1000
    accuracy = (correct_count / count) * 100
    peak_mem_mb = peak_mem / (1024 * 1024)

    print(f"  Total Processed Files:   {count:,}")
    print(f"  Total Elapsed Time:      {total_time:6.3f} seconds")
    print(f"  Average Per File:        {avg_per_file_ms:6.3f} ms")
    print(f"  Throughput:              {throughput:6.1f} files/second")
    print(f"  Peak Memory Overhead:    {peak_mem_mb:6.2f} MB")
    print(f"  Identification Accuracy: {accuracy:6.2f}% ({correct_count}/{count})")
    print(f"  Mismatches Flagged:      {mismatch_detected_count} files")

    return {
        "count": count,
        "total_time_seconds": total_time,
        "throughput_files_per_sec": throughput,
        "avg_ms_per_file": avg_per_file_ms,
        "peak_memory_mb": peak_mem_mb,
        "accuracy_percent": accuracy,
    }


def main():
    print("=" * 70)
    print("DOCUMIND AI — PHASE 2 FILE DETECTION BENCHMARK SUITE")
    print("=" * 70)

    temp_dir = Path(tempfile.mkdtemp(prefix="documind_bench_"))
    try:
        single_res = run_single_file_benchmarks(temp_dir)
        batch_100 = run_batch_benchmark(temp_dir, 100)
        batch_1000 = run_batch_benchmark(temp_dir, 1000)

        print("\n" + "=" * 70)
        print("SUMMARY RESULTS TABLE FOR DOCUMENTATION")
        print("=" * 70)
        print(f"| Test Scenario | File Count | Total Time | Throughput | Avg Latency | Peak RAM | Accuracy |")
        print(f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        print(f"| Small Batch | 100 | {batch_100['total_time_seconds']:.3f} s | {batch_100['throughput_files_per_sec']:.1f} files/s | {batch_100['avg_ms_per_file']:.2f} ms | {batch_100['peak_memory_mb']:.2f} MB | {batch_100['accuracy_percent']:.1f}% |")
        print(f"| Large Scale Batch | 1,000 | {batch_1000['total_time_seconds']:.3f} s | {batch_1000['throughput_files_per_sec']:.1f} files/s | {batch_1000['avg_ms_per_file']:.2f} ms | {batch_1000['peak_memory_mb']:.2f} MB | {batch_1000['accuracy_percent']:.1f}% |")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
