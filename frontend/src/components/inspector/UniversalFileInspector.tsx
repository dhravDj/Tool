import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  Cpu,
  Download,
  FileCode,
  FileSpreadsheet,
  FileText,
  HardDrive,
  Hash,
  Image as ImageIcon,
  Info,
  MessageSquare,
  Music,
  Package,
  Sparkles,
  Video,
  X,
} from "lucide-react";
import { ArchiveIntelligenceView } from "@/components/ArchiveIntelligenceView";
import { AudioIntelligenceView } from "@/components/AudioIntelligenceView";
import { CodeIntelligenceView } from "@/components/CodeIntelligenceView";
import { DocumentExtractionView } from "@/components/DocumentExtractionView";
import { ImageIntelligenceView } from "@/components/ImageIntelligenceView";
import { PresentationIntelligenceView } from "@/components/PresentationIntelligenceView";
import { SpreadsheetIntelligenceView } from "@/components/SpreadsheetIntelligenceView";
import { StructuredDataIntelligenceView } from "@/components/StructuredDataIntelligenceView";
import { VideoIntelligenceView } from "@/components/VideoIntelligenceView";
import { AIWorkspace } from "@/components/ai/AIWorkspace";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { FileRecordSummary } from "@/types/api";

export interface UniversalFileInspectorProps {
  file: FileRecordSummary;
  onClose?: () => void;
  isModal?: boolean;
}

export const UniversalFileInspector: React.FC<UniversalFileInspectorProps> = ({
  file,
  onClose,
  isModal = false,
}) => {
  const navigate = useNavigate();
  const { success, error } = useToast();
  const [activeTab, setActiveTab] = useState<"analysis" | "ai_chat" | "metadata">("analysis");
  const [isIndexing, setIsIndexing] = useState(false);

  // AI Indexing Status Query
  const { data: indexStatus, refetch: refetchIndexStatus } = useQuery({
    queryKey: ["fileIndexStatus", file.id],
    queryFn: () => api.getIndexStatus(file.id),
    enabled: Boolean(file.id),
  });

  const totalChunks = typeof indexStatus?.total_chunks === "number" ? indexStatus.total_chunks : 0;
  const isIndexed = indexStatus?.status === "indexed" || totalChunks > 0;

  const handleIndexForAI = async () => {
    setIsIndexing(true);
    try {
      await api.indexFile(file.id, { force: true });
      success("Indexed for AI", `${file.original_filename} is now ready for semantic search and Q&A.`);
      refetchIndexStatus();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to index file for AI.";
      error("AI Indexing Error", msg);
    } finally {
      setIsIndexing(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const ext = (
    file.detection_format_id ||
    file.actual_extension ||
    file.claimed_extension ||
    ""
  ).toLowerCase();
  const cat = file.format_category?.toLowerCase() || "";

  const isSpreadsheet =
    cat === "spreadsheet" || ["xlsx", "xls", "csv", "tsv", "ods"].includes(ext);
  const isImage =
    cat === "image" || ["png", "jpeg", "jpg", "webp", "tiff", "bmp", "gif"].includes(ext);
  const isPresentation = cat === "presentation" || ["pptx", "ppt", "odp"].includes(ext);
  const isAudio =
    cat === "audio" || ["mp3", "wav", "m4a", "aac", "flac", "ogg", "oga"].includes(ext);
  const isVideo =
    cat === "video" || ["mp4", "mkv", "mov", "avi", "webm", "m4v", "qt"].includes(ext);
  const isCode =
    cat === "code" ||
    [
      "py",
      "js",
      "ts",
      "jsx",
      "tsx",
      "html",
      "css",
      "java",
      "c",
      "cpp",
      "go",
      "rs",
      "php",
      "sql",
    ].includes(ext);
  const isStructuredData =
    cat === "structured_data" ||
    ["json", "xml", "yaml", "yml", "toml", "parquet", "pq"].includes(ext);
  const isArchive =
    cat === "archive" ||
    ["zip", "7z", "tar", "gz", "tgz", "bz2", "tbz2", "xz", "txz"].includes(ext);

  const getFormatIcon = () => {
    if (isSpreadsheet) return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
    if (isImage) return <ImageIcon className="h-5 w-5 text-purple-500" />;
    if (isPresentation) return <FileText className="h-5 w-5 text-orange-500" />;
    if (isAudio) return <Music className="h-5 w-5 text-pink-500" />;
    if (isVideo) return <Video className="h-5 w-5 text-red-500" />;
    if (isCode || isStructuredData) return <FileCode className="h-5 w-5 text-indigo-500" />;
    if (isArchive) return <Package className="h-5 w-5 text-amber-500" />;
    return <FileText className="h-5 w-5 text-blue-500" />;
  };

  const getEngineBadgeLabel = () => {
    if (isSpreadsheet) return "Phase 5 Spreadsheet Engine";
    if (isImage) return "Phase 4 Visual & OCR Engine";
    if (isPresentation) return "Phase 6 Presentation Engine";
    if (isAudio) return "Phase 7 Audio & Diarization Engine";
    if (isVideo) return "Phase 8 Video Timeline Engine";
    if (isCode) return "Phase 9 Code AST & Security Engine";
    if (isStructuredData) return "Phase 9 Structured Data Engine";
    if (isArchive) return "Phase 10 Archive & Nested Engine";
    return "Phase 3 Canonical Extraction Engine";
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-2xl border border-border shadow-xs overflow-hidden">
      {/* Universal Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-4 border-b border-border bg-card/60 backdrop-blur-xs">
        <div className="flex items-center gap-3.5 min-w-0">
          {onClose ? (
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition shrink-0"
              aria-label="Back or Close"
            >
              {isModal ? <X className="h-5 w-5" /> : <ArrowLeft className="h-5 w-5" />}
            </button>
          ) : (
            <button
              onClick={() => navigate("/files")}
              className="p-1.5 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition shrink-0"
              aria-label="Back to Library"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
          )}

          <div className="p-2.5 rounded-xl bg-muted border border-border shrink-0">
            {getFormatIcon()}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-sm sm:text-base font-bold text-foreground truncate max-w-sm sm:max-w-md">
                {file.original_filename}
              </h2>
              <Badge variant="primary" size="sm">
                {ext.toUpperCase()}
              </Badge>
              {isIndexed ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" /> AI Indexed ({totalChunks} chunks)
                </span>
              ) : (
                <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full border border-border">
                  Not Indexed
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
              <span>{formatBytes(file.file_size)}</span>
              <span>•</span>
              <span className="capitalize">{file.format_category || "Document"}</span>
              <span>•</span>
              <span className="text-[11px] font-mono">{getEngineBadgeLabel()}</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          {!isIndexed && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleIndexForAI}
              isLoading={isIndexing}
              leftIcon={<Sparkles className="h-3.5 w-3.5 text-purple-500" />}
            >
              Index for AI
            </Button>
          )}

          <a
            href={api.getFileDownloadUrl(file.id)}
            download={file.original_filename}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card hover:bg-muted text-foreground text-xs font-medium transition shadow-2xs"
            title="Download Original File"
          >
            <Download className="h-3.5 w-3.5" />
            <span className="hidden md:inline">Download</span>
          </a>

          {isModal && onClose && (
            <button
              onClick={onClose}
              className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition"
              aria-label="Close Inspector"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center px-6 border-b border-border bg-muted/20 gap-2">
        <button
          onClick={() => setActiveTab("analysis")}
          className={`flex items-center gap-2 py-3 px-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "analysis"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Cpu className="h-3.5 w-3.5" />
          Intelligence Analysis
        </button>

        <button
          onClick={() => setActiveTab("ai_chat")}
          className={`flex items-center gap-2 py-3 px-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "ai_chat"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <MessageSquare className="h-3.5 w-3.5 text-blue-500" />
          Chat &amp; Ask AI
        </button>

        <button
          onClick={() => setActiveTab("metadata")}
          className={`flex items-center gap-2 py-3 px-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "metadata"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Info className="h-3.5 w-3.5" />
          File Metadata &amp; Hashes
        </button>
      </div>

      {/* Main Inspector Body */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "analysis" && (
          <div>
            {isSpreadsheet ? (
              <SpreadsheetIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isImage ? (
              <ImageIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isPresentation ? (
              <PresentationIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isAudio ? (
              <AudioIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isVideo ? (
              <VideoIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isCode ? (
              <CodeIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isStructuredData ? (
              <StructuredDataIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : isArchive ? (
              <ArchiveIntelligenceView fileId={file.id} filename={file.original_filename} />
            ) : (
              <DocumentExtractionView fileId={file.id} filename={file.original_filename} />
            )}
          </div>
        )}

        {activeTab === "ai_chat" && (
          <div className="max-w-4xl mx-auto">
            <AIWorkspace selectedFileId={file.id} selectedFilename={file.original_filename} />
          </div>
        )}

        {activeTab === "metadata" && (
          <div className="max-w-2xl mx-auto rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4 text-xs">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Info className="h-4 w-4 text-primary" />
              Technical File Properties &amp; Verification
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-3 rounded-xl bg-muted/60 border border-border">
                <span className="text-muted-foreground text-[11px] block">File ID (UUID)</span>
                <span className="font-mono text-foreground font-medium select-all">{file.id}</span>
              </div>

              <div className="p-3 rounded-xl bg-muted/60 border border-border">
                <span className="text-muted-foreground text-[11px] block">Detected MIME Type</span>
                <span className="font-mono text-foreground font-medium">
                  {file.detected_mime_type || "application/octet-stream"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted/60 border border-border">
                <span className="text-muted-foreground text-[11px] block">File Size</span>
                <span className="text-foreground font-medium">
                  {formatBytes(file.file_size)} ({file.file_size.toLocaleString()} bytes)
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted/60 border border-border">
                <span className="text-muted-foreground text-[11px] block">Ingestion Timestamp</span>
                <span className="text-foreground font-medium">
                  {file.created_at ? new Date(file.created_at).toLocaleString() : "N/A"}
                </span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-muted/60 border border-border">
              <span className="text-muted-foreground text-[11px] flex items-center gap-1.5 mb-1">
                <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                SHA-256 Checksum Fingerprint
              </span>
              <span className="font-mono text-[11px] text-foreground select-all break-all block">
                {file.sha256}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-muted/60 border border-border">
              <span className="text-muted-foreground text-[11px] flex items-center gap-1.5 mb-1">
                <HardDrive className="h-3.5 w-3.5 text-muted-foreground" />
                Local Storage Subsystem Path
              </span>
              <span className="font-mono text-[11px] text-foreground select-all break-all block">
                {file.storage_path}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
