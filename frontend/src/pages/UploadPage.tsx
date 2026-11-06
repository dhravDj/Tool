import React, { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Copy,
  FileBox,
  FileCode,
  FileSpreadsheet,
  FileText,
  FileUp,
  FolderUp,
  Image as ImageIcon,
  Info,
  Layers,
  Loader2,
  Music,
  Package,
  ShieldAlert,
  ShieldCheck,
  UploadCloud,
  Video,
  X,
} from "lucide-react";
import { UniversalFileInspector } from "@/components/inspector/UniversalFileInspector";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { PageContainer } from "@/components/ui/PageContainer";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { DetectionResultData, FileRecordSummary } from "@/types/api";

interface DetectedFileItem {
  file: File;
  status: "pending" | "detecting" | "success" | "error";
  result?: DetectionResultData;
  error?: string;
  isDuplicate?: boolean;
  duplicateFileName?: string;
}

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error: toastError, warning } = useToast();

  const [isDragging, setIsDragging] = useState(false);
  const [queue, setQueue] = useState<DetectedFileItem[]>([]);
  const [persistToLibrary, setPersistToLibrary] = useState(true);
  const [expandedFileIndex, setExpandedFileIndex] = useState<number | null>(null);
  const [inspectingFile, setInspectingFile] = useState<FileRecordSummary | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    const itemIndex = queue.length;
    setQueue((prev) => [...prev, { file, status: "detecting" }]);

    try {
      // 1. Detect and persist
      const result = await api.detectFile(file, persistToLibrary);

      // 2. Check for duplicate warning
      let isDuplicate = false;
      let duplicateFileName: string | undefined;
      try {
        const dedupRes = await api.inspectDeduplication({
          filename: file.name,
          sha256: result.sha256,
          file_size: file.size,
        });
        if (dedupRes.action === "skip" || dedupRes.is_duplicate) {
          isDuplicate = true;
          duplicateFileName = dedupRes.existing_filename || undefined;
        }
      } catch {
        // Dedup check failure is non-fatal
      }

      setQueue((prev) =>
        prev.map((item, idx) =>
          idx === itemIndex
            ? { ...item, status: "success", result, isDuplicate, duplicateFileName }
            : item
        )
      );

      if (isDuplicate) {
        warning(
          "Potential Duplicate Detected",
          `A file with matching SHA-256 already exists (${duplicateFileName || "library"}).`
        );
      } else {
        success("Detected Successfully", `${file.name} identified as ${result.display_name}.`);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Detection failed";
      setQueue((prev) =>
        prev.map((item, idx) =>
          idx === itemIndex ? { ...item, status: "error", error: errMsg } : item
        )
      );
      toastError("Upload Failed", `${file.name}: ${errMsg}`);
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
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getFormatIcon = (cat?: string) => {
    switch (cat) {
      case "pdf":
      case "document":
        return <FileText className="h-5 w-5 text-blue-500" />;
      case "spreadsheet":
        return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
      case "image":
        return <ImageIcon className="h-5 w-5 text-purple-500" />;
      case "audio":
        return <Music className="h-5 w-5 text-pink-500" />;
      case "video":
        return <Video className="h-5 w-5 text-red-500" />;
      case "archive":
        return <Package className="h-5 w-5 text-amber-500" />;
      case "code":
      case "structured_data":
        return <FileCode className="h-5 w-5 text-indigo-500" />;
      default:
        return <FileBox className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getRecommendedAction = (cat?: string, _ext?: string) => {
    switch (cat) {
      case "spreadsheet":
        return { label: "Analyze Spreadsheet & Formulas", route: "spreadsheet" };
      case "image":
        return { label: "Analyze OCR & Scene Vision", route: "image" };
      case "presentation":
        return { label: "Extract Slides & Diagrams", route: "presentation" };
      case "audio":
        return { label: "Transcribe Speech & Diarize", route: "audio" };
      case "video":
        return { label: "Analyze Video & Keyframes", route: "video" };
      case "code":
        return { label: "Inspect AST Symbols & Security", route: "code" };
      case "structured_data":
        return { label: "Parse Schema & Hierarchy", route: "structured" };
      case "archive":
        return { label: "Inspect Nested Archive Tree", route: "archive" };
      default:
        return { label: "Extract Text & Tables", route: "document" };
    }
  };

  const openInspectorForItem = (item: DetectedFileItem) => {
    if (!item.result) return;
    const fileRecordSummary: FileRecordSummary = {
      id: item.result.persisted_file_id || item.result.sha256.slice(0, 16),
      original_filename: item.file.name,
      stored_filename: item.file.name,
      extension: item.result.extension,
      file_size: item.file.size,
      sha256: item.result.sha256,
      created_at: new Date().toISOString(),
      status: "processed",
      detection_format_id: item.result.format_id,
      claimed_extension: item.result.claimed_extension,
      actual_extension: item.result.extension,
      format_category: item.result.category,
      detected_mime_type: item.result.mime_type,
      confidence_score: item.result.confidence_score,
      confidence_level: item.result.confidence_level,
      is_mismatch: item.result.is_mismatch,
      is_corrupted: item.result.is_corrupted,
      is_suspicious: item.result.is_suspicious,
      storage_path: "",
    };
    setInspectingFile(fileRecordSummary);
  };

  return (
    <PageContainer
      title="Universal Detection & Ingestion Gateway"
      subtitle="Identify, validate, and route files to dedicated intelligence engines with zero-trust verification"
      action={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/bulk-processing")}
            leftIcon={<Layers className="h-3.5 w-3.5 text-indigo-500" />}
          >
            Bulk Processing Mode
          </Button>
        </div>
      }
    >
      {/* Zero-Trust Architecture Security Banner */}
      <div className="rounded-2xl border border-border bg-card p-4 flex items-start gap-3.5 shadow-2xs">
        <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="text-xs text-muted-foreground space-y-1">
          <p className="font-semibold text-foreground">Zero-Trust Multi-Signal Ingestion Active</p>
          <p>
            Filename extensions are never blindly trusted. Every payload undergoes 7-stage arbitration:
            magic byte headers, libmagic MIME typing, OOXML/ODF container inspection, safe structural
            heuristics, SHA-256 deduplication, and confidence scoring.
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
        className={`mt-6 border-2 border-dashed rounded-3xl p-10 text-center transition-all ${
          isDragging
            ? "border-primary bg-primary/5 scale-[0.99]"
            : "border-border bg-card/60 hover:border-primary/50"
        } shadow-2xs`}
      >
        <div className="flex flex-col items-center justify-center max-w-md mx-auto">
          <div className="p-4 rounded-2xl bg-primary/10 text-primary mb-4 shadow-xs">
            <UploadCloud className="h-10 w-10" />
          </div>
          <h3 className="text-base font-bold text-foreground tracking-tight">
            Drag &amp; drop files or folders to ingest
          </h3>
          <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
            Supports all 44+ registered formats: PDF, Word, Excel, PowerPoint, JPEG, PNG, MP3, WAV,
            MP4, MKV, Code (Python, JS, TS, C, Rust), Data (JSON, XML, YAML, Parquet), and Archives (ZIP, 7Z, TAR).
          </p>

          <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={() => fileInputRef.current?.click()}
              leftIcon={<FileUp className="h-4 w-4" />}
            >
              Browse Files
            </Button>

            <Button
              variant="outline"
              size="md"
              onClick={() => folderInputRef.current?.click()}
              leftIcon={<FolderUp className="h-4 w-4" />}
            >
              Select Directory
            </Button>

            {/* Hidden file & folder inputs */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files) handleFilesAdded(e.target.files);
              }}
            />
            <input
              ref={folderInputRef}
              type="file"
              multiple
              {...({ webkitdirectory: "", directory: "" } as any)}
              className="hidden"
              onChange={(e) => {
                if (e.target.files) handleFilesAdded(e.target.files);
              }}
            />
          </div>

          <label className="mt-4 flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none">
            <input
              type="checkbox"
              checked={persistToLibrary}
              onChange={(e) => setPersistToLibrary(e.target.checked)}
              className="rounded border-border text-primary focus:ring-primary"
            />
            <span>Persist validated files to platform library automatically</span>
          </label>
        </div>
      </div>

      {/* Detection Results & Action Routing Queue */}
      <div className="mt-8 rounded-2xl border border-border bg-card p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Ingested File Results</h3>
            {queue.length > 0 && (
              <Badge variant="primary" size="sm">
                {queue.length} {queue.length === 1 ? "file" : "files"}
              </Badge>
            )}
          </div>
          {queue.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearQueue} leftIcon={<X className="h-3.5 w-3.5" />}>
              Clear Results
            </Button>
          )}
        </div>

        {queue.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground text-xs">
            <FileUp className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p className="font-semibold text-foreground">No files evaluated in current session</p>
            <p className="mt-1">Drop files above to execute instant multi-signal format detection.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {queue.map((item, index) => {
              const res = item.result;
              const isExpanded = expandedFileIndex === index;
              const action = res ? getRecommendedAction(res.category, res.extension) : null;

              return (
                <div
                  key={`${item.file.name}-${index}`}
                  className="rounded-2xl border border-border bg-background p-4 transition-all hover:border-primary/40 shadow-2xs space-y-3"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="p-2.5 rounded-xl bg-muted text-muted-foreground shrink-0 mt-0.5">
                        {getFormatIcon(res?.category)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-xs font-bold text-foreground truncate max-w-xs md:max-w-md">
                            {item.file.name}
                          </p>
                          <span className="text-[11px] text-muted-foreground font-mono">
                            ({formatBytes(item.file.size)})
                          </span>

                          {item.status === "detecting" && (
                            <Badge variant="warning" size="sm">
                              <Loader2 className="h-3 w-3 animate-spin mr-1" />
                              Detecting
                            </Badge>
                          )}

                          {item.status === "error" && (
                            <Badge variant="danger" size="sm">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Failed
                            </Badge>
                          )}

                          {res && (
                            <>
                              <Badge variant="primary" size="sm">
                                {res.display_name}
                              </Badge>
                              <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                                {res.mime_type}
                              </span>
                              <span
                                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                  res.confidence_level === "high"
                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                    : "bg-amber-500/10 text-amber-600"
                                }`}
                              >
                                {Math.round(res.confidence_score * 100)}% Confidence
                              </span>
                            </>
                          )}
                        </div>

                        {/* Duplicate Alert */}
                        {item.isDuplicate && (
                          <div className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:text-amber-300">
                            <Copy className="h-3.5 w-3.5 shrink-0" />
                            Deduplication Warning: Identical content already exists in library (
                            {item.duplicateFileName || "previous upload"}).
                          </div>
                        )}

                        {/* Extension Mismatch / Security Alerts */}
                        {res && (res.is_mismatch || res.is_corrupted || res.is_suspicious) && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {res.is_mismatch && (
                              <div className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:text-amber-300">
                                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                                Extension Mismatch: Claimed .{res.claimed_extension || "none"}, actually .
                                {res.extension}
                              </div>
                            )}
                            {res.is_corrupted && (
                              <div className="inline-flex items-center gap-1.5 rounded-lg bg-red-500/10 border border-red-500/30 px-2.5 py-1 text-xs font-semibold text-red-600 dark:text-red-400">
                                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                                Corruption Flag: Truncated or malformed internal structure
                              </div>
                            )}
                            {res.is_suspicious && (
                              <div className="inline-flex items-center gap-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 px-2.5 py-1 text-xs font-semibold text-purple-600 dark:text-purple-400">
                                <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                                Security Flag: Executable disguise detected
                              </div>
                            )}
                          </div>
                        )}

                        {item.status === "error" && (
                          <p className="mt-1 text-xs text-red-500">{item.error}</p>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    {res && (
                      <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => openInspectorForItem(item)}
                          rightIcon={<ArrowRight className="h-3 w-3" />}
                        >
                          {action?.label || "Open Inspector"}
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setExpandedFileIndex(isExpanded ? null : index)}
                        >
                          {isExpanded ? "Hide Evidence" : "Inspect Evidence"}
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Multi-Signal Evidence Drawer */}
                  {res && isExpanded && (
                    <div className="pt-3 border-t border-border grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="rounded-xl bg-card p-3 border border-border">
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
                          <CheckCircle className="h-4 w-4 text-emerald-500" />
                          Detection Signals Log
                        </h4>
                        <div className="space-y-1.5">
                          {res.evidence.map((ev, evIdx) => (
                            <div
                              key={evIdx}
                              className="rounded-lg bg-background p-2 border border-border/60 text-[11px] flex justify-between"
                            >
                              <span className="font-semibold uppercase text-foreground">{ev.signal}</span>
                              <span className="text-muted-foreground font-mono">{ev.details}</span>
                              <span className="text-emerald-600 font-medium">
                                {Math.round(ev.confidence_score * 100)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl bg-card p-3 border border-border space-y-2">
                        <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                          <Info className="h-4 w-4 text-primary" />
                          Technical Specifications
                        </h4>
                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                          <div>
                            <span className="text-muted-foreground">Category:</span>{" "}
                            <span className="font-medium capitalize text-foreground">{res.category}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Support Status:</span>{" "}
                            <span className="font-medium uppercase text-emerald-600">{res.support_status}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Detection Time:</span>{" "}
                            <span className="font-mono text-foreground">{res.detection_duration_ms.toFixed(1)} ms</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">SHA-256:</span>{" "}
                            <span className="font-mono text-[10px] text-foreground truncate block">
                              {res.sha256.slice(0, 16)}...
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Universal File Inspector Modal */}
      {inspectingFile && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-150">
          <div className="w-full max-w-7xl h-[92vh] flex flex-col">
            <UniversalFileInspector
              file={inspectingFile}
              onClose={() => setInspectingFile(null)}
              isModal={true}
            />
          </div>
        </div>
      )}
    </PageContainer>
  );
};
