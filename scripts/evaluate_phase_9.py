"""Comprehensive Benchmark and Evaluation Script for Phase 9: Code & Structured Data Intelligence."""

import asyncio
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.modules.code_intelligence.pipeline import code_pipeline
from app.modules.structured_data_intelligence.pipeline import structured_pipeline

CODE_FIXTURES = Path(__file__).parent.parent / "backend" / "tests" / "fixtures" / "code"
STRUCT_FIXTURES = Path(__file__).parent.parent / "backend" / "tests" / "fixtures" / "structured"


async def benchmark_code_engine() -> dict[str, Any]:
    print("\n=======================================================")
    print("  PHASE 9 BENCHMARK: CODE INTELLIGENCE ENGINE (14 LANGS)")
    print("=======================================================")

    results: list[dict[str, Any]] = []

    files = sorted(CODE_FIXTURES.glob("*.*"))
    for file_path in files:
        if file_path.suffix == ".pyc":
            continue

        tracemalloc.start()
        t0 = time.perf_counter()

        doc = await code_pipeline.analyze_code(
            file_path=file_path,
            file_id=f"bench_{file_path.stem}",
            original_filename=file_path.name,
        )

        duration_ms = (time.perf_counter() - t0) * 1000
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        res_entry = {
            "filename": file_path.name,
            "language": doc.language,
            "lines": doc.metrics.total_lines,
            "symbols": len(doc.symbols),
            "imports": len(doc.imports),
            "diagnostics": len(doc.diagnostics),
            "syntax_valid": doc.syntax_validation.is_valid,
            "latency_ms": round(duration_ms, 2),
            "peak_mem_kb": round(peak_mem / 1024, 2),
        }
        results.append(res_entry)

        status_str = "VALID" if doc.syntax_validation.is_valid else "SYNTAX_ERROR"
        print(
            f"  [{doc.language.upper():<5}] {file_path.name:<30} "
            f"| Lines: {doc.metrics.total_lines:<4} | Symbols: {len(doc.symbols):<3} "
            f"| Diags: {len(doc.diagnostics):<2} | Status: {status_str:<12} "
            f"| {duration_ms:>6.2f} ms | {peak_mem / 1024:>6.1f} KB"
        )

    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0
    total_symbols = sum(r["symbols"] for r in results)
    total_diagnostics = sum(r["diagnostics"] for r in results)

    return {
        "files_tested": len(results),
        "avg_latency_ms": round(avg_latency, 2),
        "total_symbols_extracted": total_symbols,
        "total_diagnostics_detected": total_diagnostics,
        "detailed_results": results,
    }


async def benchmark_structured_engine() -> dict[str, Any]:
    print("\n=======================================================")
    print("  PHASE 9 BENCHMARK: STRUCTURED DATA ENGINE (5 FORMATS)")
    print("=======================================================")

    results: list[dict[str, Any]] = []

    files = sorted(STRUCT_FIXTURES.glob("*.*"))
    for file_path in files:
        tracemalloc.start()
        t0 = time.perf_counter()

        doc = await structured_pipeline.analyze_structured_data(
            file_path=file_path,
            file_id=f"bench_{file_path.stem}",
            original_filename=file_path.name,
        )

        duration_ms = (time.perf_counter() - t0) * 1000
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        security_alerts = len(doc.validation_results.security_warnings)
        dup_keys = len(doc.validation_results.duplicate_keys)

        res_entry = {
            "filename": file_path.name,
            "format": doc.format,
            "root_type": doc.root_type,
            "rows": doc.data_profile.total_rows,
            "columns": len(doc.data_profile.column_profiles),
            "security_alerts": security_alerts,
            "duplicate_keys": dup_keys,
            "is_valid": doc.validation_results.is_valid,
            "latency_ms": round(duration_ms, 2),
            "peak_mem_kb": round(peak_mem / 1024, 2),
        }
        results.append(res_entry)

        valid_str = "VALID" if doc.validation_results.is_valid else "INVALID/BLOCKED"
        print(
            f"  [{doc.format.upper():<7}] {file_path.name:<25} "
            f"| Rows: {doc.data_profile.total_rows:<5} | Cols: {len(doc.data_profile.column_profiles):<3} "
            f"| Sec: {security_alerts:<2} | DupKeys: {dup_keys:<2} | Status: {valid_str:<14} "
            f"| {duration_ms:>6.2f} ms | {peak_mem / 1024:>6.1f} KB"
        )

    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0

    return {
        "files_tested": len(results),
        "avg_latency_ms": round(avg_latency, 2),
        "detailed_results": results,
    }


async def main() -> None:
    code_summary = await benchmark_code_engine()
    struct_summary = await benchmark_structured_engine()

    print("\n=======================================================")
    print("  PHASE 9 BENCHMARK SUMMARY")
    print("=======================================================")
    print(f"  Code Files Evaluated:        {code_summary['files_tested']}")
    print(f"  Code Avg Latency:            {code_summary['avg_latency_ms']} ms")
    print(f"  Code Symbols Extracted:      {code_summary['total_symbols_extracted']}")
    print(f"  Code Diagnostics Found:      {code_summary['total_diagnostics_detected']}")
    print("  -----------------------------------------------------")
    print(f"  Structured Files Evaluated:  {struct_summary['files_tested']}")
    print(f"  Structured Avg Latency:      {struct_summary['avg_latency_ms']} ms")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
