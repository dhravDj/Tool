#!/usr/bin/env python3
"""Performance profiling and throughput benchmark for Image & Visual Intelligence Engine."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from PIL import Image

from app.modules.image_intelligence.pipeline import ImageIntelligencePipeline


def generate_benchmark_specimens(temp_dir: Path) -> dict[str, Path]:
    """Generate representative image files for benchmarking."""
    specimens: dict[str, Path] = {}

    # 1. PNG (1080p high resolution)
    png_path = temp_dir / "bench_1080p.png"
    Image.new("RGB", (1920, 1080), color=(60, 140, 220)).save(png_path, "PNG")
    specimens["png_1080p"] = png_path

    # 2. JPEG (720p photo-like)
    jpg_path = temp_dir / "bench_720p.jpg"
    Image.new("RGB", (1280, 720), color=(180, 90, 40)).save(jpg_path, "JPEG")
    specimens["jpeg_720p"] = jpg_path

    # 3. WEBP (Square UI asset)
    webp_path = temp_dir / "bench_square.webp"
    Image.new("RGB", (512, 512), color=(50, 180, 80)).save(webp_path, "WEBP")
    specimens["webp_square"] = webp_path

    # 4. TIFF (Document scan)
    tiff_path = temp_dir / "bench_scan.tiff"
    Image.new("RGB", (800, 1100), color=(245, 245, 245)).save(tiff_path, "TIFF")
    specimens["tiff_scan"] = tiff_path

    # 5. BMP (Raw bitmap)
    bmp_path = temp_dir / "bench_bitmap.bmp"
    Image.new("RGB", (640, 480), color=(100, 100, 100)).save(bmp_path, "BMP")
    specimens["bmp_raw"] = bmp_path

    # 6. SVG (Vector graphic)
    svg_path = temp_dir / "bench_vector.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
      <rect width="800" height="600" fill="#e2e8f0"/>
      <circle cx="400" cy="300" r="120" fill="#2563eb"/>
      <text x="400" y="300" font-size="24" text-anchor="middle" fill="#ffffff">Benchmark Diagram</text>
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")
    specimens["svg_vector"] = svg_path

    return specimens


def run_benchmark():
    print("=" * 60)
    print(" DocuMind AI — Image Intelligence Performance Benchmark")
    print("=" * 60)

    pipeline = ImageIntelligencePipeline()
    results: dict[str, dict] = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir)
        specimens = generate_benchmark_specimens(temp_path)

        for label, file_path in specimens.items():
            format_id = file_path.suffix.lstrip(".").lower()
            if format_id in ("jpg", "jpeg"):
                format_id = "jpeg"

            file_size_kb = round(file_path.stat().st_size / 1024, 2)
            latencies = []

            # 5 iterations per format
            for i in range(5):
                t0 = time.perf_counter()
                doc, manifest = pipeline.process_image_path(
                    file_path=file_path,
                    file_id=f"bench-{label}-{i}",
                    filename=file_path.name,
                    format_id=format_id,
                )
                duration_ms = (time.perf_counter() - t0) * 1000
                latencies.append(duration_ms)

            avg_ms = round(sum(latencies) / len(latencies), 2)
            min_ms = round(min(latencies), 2)
            max_ms = round(max(latencies), 2)
            fps = round(1000.0 / avg_ms, 2)

            results[label] = {
                "format": format_id,
                "file_size_kb": file_size_kb,
                "avg_latency_ms": avg_ms,
                "min_latency_ms": min_ms,
                "max_latency_ms": max_ms,
                "throughput_images_per_sec": fps,
                "regions_detected": len(doc.regions),
                "scene_type": doc.analysis.scene_type,
            }

            print(f"[*] {label:<16} | Size: {file_size_kb:>7.1f} KB | Avg: {avg_ms:>6.2f} ms | Speed: {fps:>5.1f} img/s")

    report_path = Path("reports/IMAGE_INTELLIGENCE_BENCHMARK.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[+] Benchmark metrics saved to {report_path}")


if __name__ == "__main__":
    run_benchmark()
