import React, { useCallback, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  FileUp,
  Info,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { api } from "@/services/api";
import { DetectionResultData } from "@/types/api";

interface DetectedFileItem {
  file: File;
  status: "pending" | "detecting" | "success" | "error";
  result?: DetectionResultData;
  error?: string;
}

export const UploadPage: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [queue, setQueue] = useState<DetectedFileItem[]>([]);
  const [persistToLibrary, setPersistToLibrary] = useState(true);
  const [expandedFileIndex, setExpandedFileIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    const itemIndex = queue.length;
    setQueue((prev) => [...prev, { file, status: "detecting" }]);

    try {
      const result = await api.detectFile(file, persistToLibrary);
      setQueue((prev) =>
        prev.map((item, idx) => (idx === itemIndex ? { ...item, status: "success", result } : item))
      );
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Detection failed";
      setQueue((prev) =>
        prev.map((item, idx) => (idx === itemIndex ? { ...item, status: "error", error: errMsg } : item))
      );
    }
  };

  const handleFilesAdded = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      if (fileArray.length === 0) return;

      for (const file of fileArray) {
        await processFile(file);
      }
    },
    [persistToLibrary, queue.length]
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const clearQueue = () => {
    setQueue([]);
    setExpandedFileIndex(null);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <PageContainer
      title="Universal Detection & Ingestion Gateway"
      subtitle="Analyze, detect, and verify file formats via multi-signal binary, MIME, container, and text heuristics"
    >
      {/* Zero-Trust Architecture Security Banner */}
      <div className="rounded-xl border border-border bg-card p-4 flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
        <div className="text-xs text-muted-foreground space-y-1">
          <p className="font-semibold text-foreground">Zero-Trust Multi-Signal Detection Active</p>
          <p>
            Filename extensions are never trusted. Files are analyzed through an 7-stage pipeline:
            filesystem validation, magic-byte inspection, libmagic MIME typing, internal container
            manifest parsing, safe structural text heuristics, and confidence scoring with mismatch
            detection.
          </p>
        </div>
      </div>

      {/* Upload & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`mt-6 border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
          isDragging
            ? "border-primary bg-primary/5 scale-[0.99]"
            : "border-border bg-card/60 hover:border-primary/50"
        }`}
      >
        <div className="flex flex-col items-center justify-center max-w-md mx-auto">
          <div className="p-4 rounded-full bg-primary/10 text-primary mb-4">
            <UploadCloud className="h-10 w-10" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">
            Drag and drop files to detect
          </h3>
          <p className="text-xs text-muted-foreground mt-2">
            Inspect any file format: PDF, Office documents, media, archives, code, or unknown binaries.
          </p>

          <div className="mt-6 flex flex-col sm:flex-row items-center gap-4">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="cursor-pointer rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-primary/90 transition"
            >
              Browse Local Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files) {
                  handleFilesAdded(e.target.files);
                }
              }}
            />

            <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none">
              <input
                type="checkbox"
                checked={persistToLibrary}
                onChange={(e) => setPersistToLibrary(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary"
              />
              Persist identified files to storage library
            </label>
          </div>
        </div>
      </div>

      {/* Detection Queue & Results */}
      <div className="mt-8 rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Detection Results</h3>
            {queue.length > 0 && (
              <span className="rounded-full bg-primary/10 text-primary px-2 py-0.5 text-[11px] font-semibold">
                {queue.length} {queue.length === 1 ? "file" : "files"}
              </span>
            )}
          </div>
          {queue.length > 0 && (
            <button
              onClick={clearQueue}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition"
            >
              <X className="h-3.5 w-3.5" />
              Clear Results
            </button>
          )}
        </div>

        {queue.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground text-xs">
            <FileUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="font-medium text-foreground">No files evaluated yet</p>
            <p className="mt-1">Drag and drop or select files above to run Universal Detection.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {queue.map((item, index) => {
              const res = item.result;
              const isExpanded = expandedFileIndex === index;

              return (
                <div
                  key={`${item.file.name}-${index}`}
                  className="rounded-lg border border-border bg-background p-4 transition hover:border-primary/40"
                >
                  {/* Summary Bar */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-muted text-muted-foreground shrink-0 mt-0.5">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-medium text-foreground truncate max-w-xs md:max-w-md">
                            {item.file.name}
                          </p>
                          <span className="text-[11px] text-muted-foreground">
                            ({formatBytes(item.file.size)})
                          </span>

                          {/* Status Badge */}
                          {item.status === "detecting" && (
                            <span className="inline-flex items-center gap-1 rounded bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-500">
                              <Loader2 className="h-3 w-3 animate-spin" /> Detecting
                            </span>
                          )}
                          {item.status === "error" && (
                            <span className="inline-flex items-center gap-1 rounded bg-red-500/10 px-2 py-0.5 text-[11px] font-medium text-red-500">
                              <AlertCircle className="h-3 w-3" /> Error
                            </span>
                          )}
                          {res && (
                            <>
                              <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                                {res.display_name}
                              </span>
                              <span className="rounded bg-muted px-2 py-0.5 text-[11px] font-mono text-muted-foreground">
                                {res.mime_type}
                              </span>
                              <span
                                className={`rounded px-2 py-0.5 text-[11px] font-medium ${
                                  res.confidence_level === "high"
                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                    : res.confidence_level === "medium"
                                      ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                                      : "bg-red-500/10 text-red-500"
                                }`}
                              >
                                {Math.round(res.confidence_score * 100)}% Confidence (
                                {res.confidence_level.toUpperCase()})
                              </span>
                            </>
                          )}
                        </div>

                        {/* Extension Mismatch / Corruption Alert Banner */}
                        {res && (res.is_mismatch || res.is_corrupted || res.is_suspicious) && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {res.is_mismatch && (
                              <div className="inline-flex items-center gap-1.5 rounded-md bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:text-amber-300">
                                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                                Extension Mismatch: Claimed .{res.claimed_extension || "none"} but file is actually .{res.extension} ({res.canonical_name})
                              </div>
                            )}
                            {res.is_corrupted && (
                              <div className="inline-flex items-center gap-1.5 rounded-md bg-red-500/10 border border-red-500/30 px-2.5 py-1 text-xs font-semibold text-red-600 dark:text-red-400">
                                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                                Corruption Flag: Truncated or malformed file structure detected
                              </div>
                            )}
                            {res.is_suspicious && (
                              <div className="inline-flex items-center gap-1.5 rounded-md bg-purple-500/10 border border-purple-500/30 px-2.5 py-1 text-xs font-semibold text-purple-600 dark:text-purple-400">
                                <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                                Security Flag: Executable or polyglot masquerading as innocuous format
                              </div>
                            )}
                          </div>
                        )}

                        {item.status === "error" && (
                          <p className="mt-1 text-xs text-red-500">{item.error}</p>
                        )}
                      </div>
                    </div>

                    {res && (
                      <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                        <span className="text-[11px] text-muted-foreground">
                          {res.detection_duration_ms.toFixed(1)} ms
                        </span>
                        <button
                          type="button"
                          onClick={() => setExpandedFileIndex(isExpanded ? null : index)}
                          className="flex items-center gap-1 rounded border border-border px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground transition"
                        >
                          {isExpanded ? (
                            <>
                              Hide Details <ChevronUp className="h-3.5 w-3.5" />
                            </>
                          ) : (
                            <>
                              Inspect Evidence <ChevronDown className="h-3.5 w-3.5" />
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Expanded Multi-Signal Inspection View */}
                  {res && isExpanded && (
                    <div className="mt-4 pt-4 border-t border-border grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      {/* Left: Signal Evidence Checklist */}
                      <div className="rounded-lg bg-card p-3 border border-border/60">
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
                          <CheckCircle className="h-4 w-4 text-emerald-500" />
                          Multi-Signal Detection Evidence
                        </h4>
                        <div className="space-y-2">
                          {res.evidence.map((ev, evIdx) => (
                            <div
                              key={evIdx}
                              className="rounded bg-background p-2 border border-border/40 text-[11px]"
                            >
                              <div className="flex items-center justify-between text-muted-foreground">
                                <span className="font-semibold uppercase text-foreground">
                                  {ev.signal}
                                </span>
                                <span>{Math.round(ev.confidence_score * 100)}% score</span>
                              </div>
                              <p className="mt-0.5 text-foreground/90 font-mono text-[10px]">
                                {ev.details}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Right: Technical Attributes & Heuristics */}
                      <div className="rounded-lg bg-card p-3 border border-border/60 space-y-3">
                        <div>
                          <h4 className="font-semibold text-foreground mb-1.5 flex items-center gap-1.5">
                            <Info className="h-4 w-4 text-primary" />
                            Technical File Attributes
                          </h4>
                          <div className="grid grid-cols-2 gap-2 text-[11px]">
                            <div>
                              <span className="text-muted-foreground">Category:</span>{" "}
                              <span className="font-medium capitalize">{res.category}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Support Status:</span>{" "}
                              <span className="font-medium uppercase">{res.support_status}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Container:</span>{" "}
                              <span>{res.is_container ? res.container_type || "Yes" : "No"}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">SHA-256:</span>{" "}
                              <span className="font-mono text-[10px] truncate block" title={res.sha256}>
                                {res.sha256.slice(0, 16)}...
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Metadata Extracted */}
                        {Object.keys(res.metadata).length > 0 && (
                          <div className="pt-2 border-t border-border/60">
                            <span className="text-muted-foreground font-semibold block mb-1">
                              Safe Header Metadata:
                            </span>
                            <pre className="bg-background rounded p-2 text-[10px] font-mono text-muted-foreground overflow-x-auto max-h-32">
                              {JSON.stringify(res.metadata, null, 2)}
                            </pre>
                          </div>
                        )}

                        {/* Detection Warnings */}
                        {res.warnings.length > 0 && (
                          <div className="pt-2 border-t border-border/60">
                            <span className="text-amber-500 font-semibold block mb-1">
                              Warnings:
                            </span>
                            <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-amber-600 dark:text-amber-400">
                              {res.warnings.map((w, wIdx) => (
                                <li key={wIdx}>{w}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
};
