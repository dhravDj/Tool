"""Automated performance and accuracy evaluation benchmark for Phase 7: Audio Intelligence."""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import psutil
from app.modules.audio_intelligence.pipeline import audio_pipeline

backend_fixtures = Path(__file__).parent.parent / "backend" / "tests" / "fixtures" / "audio"
if backend_fixtures.exists():
    FIXTURES_DIR = backend_fixtures
else:
    FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "audio"


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
        ("speech_english.wav", "speech_english.txt"),
        ("speech_hindi.wav", "speech_hindi.txt"),
        ("speech_hinglish.mp3", "speech_hinglish.txt"),
        ("conversation_multispeaker.wav", "conversation_multispeaker.txt"),
        ("speech_lossless.flac", "speech_lossless.txt"),
        ("speech_vorbis.ogg", "speech_vorbis.txt"),
        ("speech_m4a.m4a", "speech_m4a.txt"),
        ("speech_adts.aac", "speech_adts.txt"),
        ("long_recording.wav", "long_recording.txt"),
        ("pure_silence.wav", None),
        ("harmonic_music.mp3", None),
    ]

    total_proc_time = 0.0
    total_audio_duration = 0.0

    print("Running Audio Intelligence Benchmarks...")
    print("-" * 80)
    print(
        f"{'Fixture':<30} | {'Duration':<8} | {'Latency':<9} | {'RTF':<7} | {'WER':<6} | {'CER':<6}"
    )
    print("-" * 80)

    for audio_file, txt_file in fixtures:
        audio_path = FIXTURES_DIR / audio_file
        if not audio_path.exists():
            continue

        ref_text = ""
        if txt_file:
            ref_path = FIXTURES_DIR / txt_file
            if ref_path.exists():
                ref_text = ref_path.read_text(encoding="utf-8").strip()

        t0 = time.perf_counter()
        doc, _ = await audio_pipeline.analyze_audio(
            file_path=audio_path,
            file_id="bench_id",
            original_filename=audio_file,
        )
        t_elapsed = time.perf_counter() - t0

        duration = doc.duration
        rtf = t_elapsed / max(0.01, duration) if duration > 0 else 0.0

        wer = calculate_wer(ref_text, doc.transcript) if ref_text else 0.0
        cer = calculate_cer(ref_text, doc.transcript) if ref_text else 0.0

        rss_mb = process.memory_info().rss / (1024 * 1024)

        total_proc_time += t_elapsed
        total_audio_duration += duration

        entry = {
            "fixture": audio_file,
            "format": doc.format,
            "duration": round(duration, 2),
            "latency_ms": round(t_elapsed * 1000, 2),
            "rtf": round(rtf, 4),
            "wer": round(wer, 4),
            "cer": round(cer, 4),
            "rss_mb": round(rss_mb, 2),
            "segments": len(doc.segments),
            "speakers": len(doc.speakers),
            "events": len(doc.events),
        }
        results.append(entry)

        print(
            f"{audio_file:<30} | {duration:<6.1f}s | {t_elapsed*1000:<7.2f}ms | {rtf:<7.4f} | {wer:<6.2f} | {cer:<6.2f}"
        )

    avg_rtf = total_proc_time / max(0.01, total_audio_duration)
    summary = {
        "total_fixtures": len(results),
        "total_audio_duration_seconds": round(total_audio_duration, 2),
        "total_processing_time_seconds": round(total_proc_time, 3),
        "average_real_time_factor": round(avg_rtf, 4),
        "peak_rss_mb": round(max(r["rss_mb"] for r in results), 2),
        "detailed_results": results,
    }
    return summary


if __name__ == "__main__":
    report = asyncio.run(run_benchmarks())
    print("\nBenchmark Summary:")
    print(json.dumps(report, indent=2))
