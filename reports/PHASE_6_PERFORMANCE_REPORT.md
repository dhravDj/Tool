# DocuMind AI — Phase 6 Performance & Benchmark Report

**Phase:** Phase 6 — Presentation Intelligence  
**Date:** 2026-11-06T06:55:00 UTC  
**Hardware Environment:** AMD Ryzen 7 5800H (8 cores / 16 threads @ 3.2–4.4 GHz) | 16 GB DDR4 | Linux Ubuntu 26.04 x86_64  
**Engine:** Python 3.13.15, `python-pptx` 1.0.2, `defusedxml` 0.7.1, `olefile` 0.47  

---

## 1. Executive Performance Summary

- **Total Presentation Fixtures Benchmarked:** 11 presentations across PPTX, PPT, and ODP.
- **Total Slides Processed:** 15 slides.
- **Average Extraction Latency:** **8.10 ms** per presentation.
- **Fastest Processing Time:** **0.96 ms** (`odp_text_tables.odp`).
- **Slowest Processing Time:** **15.61 ms** (`pptx_basic_text.pptx`).
- **Peak RSS Memory Footprint:** **91.30 MB**.
- **Hardware Acceleration:** Native CPU execution; zero GPU requirement.

---

## 2. Granular Fixture Performance Breakdown

| Test Fixture | Format | Slide Count | Processing Latency | Peak Process RSS | Features Processed |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `pptx_basic_text.pptx` | PPTX | 2 | 15.61 ms | 85.38 MB | Title & content layouts, text frames |
| `pptx_nested_bullets.pptx` | PPTX | 1 | 9.21 ms | 86.16 MB | 3-tier bullet hierarchy (levels 0, 1, 2) |
| `pptx_tables.pptx` | PPTX | 1 | 6.84 ms | 87.08 MB | 4x3 table, cell coordinates, headers |
| `pptx_native_charts.pptx` | PPTX | 1 | 7.54 ms | 88.05 MB | Clustered column chart, 4 categories, 2 series |
| `pptx_images.pptx` | PPTX | 1 | 11.98 ms | 89.22 MB | Embedded PNG asset, SHA256 checksumming |
| `pptx_speaker_notes.pptx` | PPTX | 1 | 9.15 ms | 89.25 MB | Slide notes extraction & word counting |
| `pptx_grouped_shapes.pptx` | PPTX | 1 | 7.21 ms | 89.30 MB | Grouped shapes, right arrow connector |
| `pptx_hidden_slides.pptx` | PPTX | 3 | 9.89 ms | 89.65 MB | Multi-slide flow, hidden slide tracking |
| `pptx_unicode_hindi.pptx` | PPTX | 1 | 8.96 ms | 90.55 MB | Multilingual Devanagari Unicode text |
| `odp_text_tables.odp` | ODP | 2 | 0.96 ms | 90.68 MB | XML streaming, draw:page, table:table |
| `legacy_powerpoint.ppt` | PPT | 1 | 1.77 ms | 91.30 MB | Native OLE2 stream parser, TextBytesAtom |

---

## 3. Resource & Scaling Analysis

1. **CPU & Memory Efficiency:**
   - The engine operates with low memory overhead (<100 MB RSS).
   - In-memory parsing avoids disk bloat; temporary files are only created when sandboxed LibreOffice conversion is invoked.
2. **Asynchronous Non-Blocking Workers:**
   - All I/O operations (file reading, storage writes, database transactions) are asynchronous.
   - Workers remain responsive under concurrent presentation ingestion.
3. **Storage Deduplication:**
   - Visual media assets are hashed via SHA256, preventing duplicate storage of recurring logos, backgrounds, or templates across presentation batches.
