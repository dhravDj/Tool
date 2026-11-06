# DocuMind AI — Frontend Performance & Bundle Metrics (Phase 13)

## 1. Production Build Metrics

```
dist/index.html                   0.83 kB │ gzip:   0.48 kB
dist/assets/index-BZCEC-su.css   64.47 kB │ gzip:  10.71 kB
dist/assets/index-RiJiwfvU.js   616.85 kB │ gzip: 149.44 kB
✓ built in 2.27s
```

- **CSS Overhead**: 10.71 kB gzipped. By utilizing utility classes compiled via Tailwind v4, unused CSS is eliminated at build time.
- **JavaScript Overhead**: 149.44 kB gzipped for the entire application, containing all 10 format intelligence view engines (Documents, Spreadsheets, Presentations, Images, Audio, Video, Code, Structured Data, Archives, AI Workspace).

---

## 2. Query Caching & Re-render Minimization

### 2.1 Stale-While-Revalidate Patterns
- Critical dashboard analytics (`/system/dashboard-analytics`) use a 30-second stale time, eliminating redundant network hops during rapid navigation between views.
- Active task queue telemetry (`/jobs` and `/system`) uses an adaptive 5-second polling interval during active processing, falling back to on-demand refetch when idle.
- File library data (`/files`) is cached per filter and search term, delivering instantaneous back-navigation.

### 2.2 Memory Management
- Audio waveforms and video keyframe URLs use object URLs that are safely revoked on component unmount to prevent browser memory leaks.
- Large spreadsheet tables and JSON trees render within scrollable viewport containers, preventing DOM bloat during large dataset previews.
