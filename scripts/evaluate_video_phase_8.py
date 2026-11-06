"""Automated performance and accuracy evaluation benchmark for Phase 8: Video Intelligence."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import psutil

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.modules.video_intelligence.pipeline import video_pipeline

FIXTURES_DIR = Path(__file__).parent.parent / "backend" / "tests" / "fixtures" / "video"


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate normalized Word Error Rate (WER) using Levenshtein distance."""
    r = reference.lower().split()
    h = hypothesis.lower().split()

    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    return float(d[len(r)][len(h)]) / max(1.0, float(len(r)))


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculate normalized Character Error Rate (CER) using Levenshtein distance."""
    r = list(reference.strip().lower())
    h = list(hypothesis.strip().lower())

    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    return float(d[len(r)][len(h)]) / max(1.0, float(len(r)))


async def run_benchmarks() -> dict[str, Any]:
    process = psutil.Process(os.getpid())
    results: list[dict[str, Any]] = []

    fixtures = [
        ("video_speech_english.mp4", "video_speech_english.txt", 1),
        ("video_speech_hindi.mkv", "video_speech_hindi.txt", 1),
        ("video_no_audio.mp4", None, 1),
        ("video_multiscene.mov", None, 3),
        ("video_fade_transition.webm", None, 2),
        ("video_moving_object.avi", None, 1),
        ("video_short_clip.mp4", None, 1),
    ]

    total_proc_time = 0.0
    total_video_duration = 0.0

    print("Running Phase 8 Video Intelligence Benchmarks...")
    print("-" * 90)
    print(
        f"{'Fixture':<28} | {'Dur':<6} | {'Latency':<9} | {'RTF':<7} | {'Scenes':<7} | {'Tracks':<6} | {'WER':<5} | {'CER':<5}"
    )
    print("-" * 90)

    for video_file, txt_file, expected_min_scenes in fixtures:
        video_path = FIXTURES_DIR / video_file
        if not video_path.exists():
            continue

        ref_text = ""
        if txt_file:
            ref_path = FIXTURES_DIR / txt_file
            if ref_path.exists():
                ref_text = ref_path.read_text(encoding="utf-8").strip()

        t0 = time.perf_counter()
        doc, _ = await video_pipeline.analyze_video(
            file_path=video_path,
            file_id=f"bench_{video_file}",
            original_filename=video_file,
            options={
                "run_tracking": True,
                "run_ocr": True,
                "run_audio": True,
            },
        )
        t_elapsed = time.perf_counter() - t0

        duration = doc.duration
        rtf = t_elapsed / max(0.01, duration) if duration > 0 else 0.0

        wer = calculate_wer(ref_text, doc.transcript) if ref_text and doc.transcript else (0.0 if not ref_text else 1.0)
        cer = calculate_cer(ref_text, doc.transcript) if ref_text and doc.transcript else (0.0 if not ref_text else 1.0)

        rss_mb = process.memory_info().rss / (1024 * 1024)

        total_proc_time += t_elapsed
        total_video_duration += duration

        entry = {
            "fixture": video_file,
            "format": doc.format,
            "duration": round(duration, 2),
            "latency_ms": round(t_elapsed * 1000, 2),
            "rtf": round(rtf, 4),
            "scenes_detected": len(doc.scenes),
            "expected_min_scenes": expected_min_scenes,
            "keyframes": len(doc.keyframes),
            "tracks": len(doc.tracks),
            "events": len(doc.timeline),
            "wer": round(wer, 4),
            "cer": round(cer, 4),
            "rss_mb": round(rss_mb, 2),
        }
        results.append(entry)

        print(
            f"{video_file:<28} | {duration:<5.1f}s | {t_elapsed*1000:<7.2f}ms | {rtf:<7.4f} | {len(doc.scenes):<7} | {len(doc.tracks):<6} | {wer:<5.2f} | {cer:<5.2f}"
        )

    avg_rtf = total_proc_time / max(0.01, total_video_duration)
    summary = {
        "total_fixtures": len(results),
        "total_video_duration_seconds": round(total_video_duration, 2),
        "total_processing_time_seconds": round(total_proc_time, 3),
        "average_real_time_factor": round(avg_rtf, 4),
        "peak_rss_mb": round(max(r["rss_mb"] for r in results), 2),
        "detailed_results": results,
    }
    return summary


if __name__ == "__main__":
    report = asyncio.run(run_benchmarks())
    print("-" * 90)
    print("\nBenchmark Summary:")
    print(json.dumps(report, indent=2))
