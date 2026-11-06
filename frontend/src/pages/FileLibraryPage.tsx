import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  CheckCircle,
  FileBox,
  FileCode,
  Files,
  FileSpreadsheet,
  FileText,
  Filter,
  Hash,
  Image as ImageIcon,
  Info,
  Music,
  Package,
  Search,
  Video,
  X,
} from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { DocumentExtractionView } from "@/components/DocumentExtractionView";
import { ImageIntelligenceView } from "@/components/ImageIntelligenceView";
import { PresentationIntelligenceView } from "@/components/PresentationIntelligenceView";
import { SpreadsheetIntelligenceView } from "@/components/SpreadsheetIntelligenceView";
import { api } from "@/services/api";
import { FileRecordSummary, FormatDetailData } from "@/types/api";

export const FileLibraryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"files" | "registry">("files");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [inspectingFile, setInspectingFile] = useState<FileRecordSummary | null>(null);
  const [modalTab, setModalTab] = useState<
    "extraction" | "image_intelligence" | "spreadsheet_intelligence" | "presentation_intelligence" | "detection"
  >("extraction");

  // Queries
  const {
    data: files,
    isLoading: filesLoading,
    error: filesError,
    refetch: refetchFiles,
  } = useQuery({
    queryKey: ["files"],
    queryFn: () => api.getFiles(50, 0),
  });

  const {
    data: formatRegistry,
    isLoading: registryLoading,
    error: registryError,
  } = useQuery({
    queryKey: ["formats", selectedCategory],
    queryFn: () => api.getFormats(selectedCategory === "all" ? undefined : selectedCategory),
  });

  const categories = [
    "all",
    "document",
    "pdf",
    "spreadsheet",
    "presentation",
    "image",
    "audio",
    "video",
    "archive",
    "code",
    "structured_data",
    "email",
    "ebook",
    "font",
    "executable",
    "other_binary",
  ];

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case "pdf":
      case "document":
        return <FileText className="h-4 w-4 text-blue-500" />;
      case "spreadsheet":
        return <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
      case "image":
        return <ImageIcon className="h-4 w-4 text-purple-500" />;
      case "audio":
        return <Music className="h-4 w-4 text-pink-500" />;
      case "video":
        return <Video className="h-4 w-4 text-red-500" />;
      case "archive":
        return <Package className="h-4 w-4 text-amber-500" />;
      case "code":
      case "structured_data":
        return <FileCode className="h-4 w-4 text-indigo-500" />;
      default:
        return <FileBox className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const filteredFiles = (files || []).filter((f) => {
    const matchesSearch =
      f.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.sha256.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (f.detected_mime_type && f.detected_mime_type.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (f.detection_format_id && f.detection_format_id.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCat =
      selectedCategory === "all" ||
      f.format_category === selectedCategory ||
      (selectedCategory === "document" && f.format_category === "pdf");

    return matchesSearch && matchesCat;
  });

  const isSpreadsheet = (f: FileRecordSummary) =>
    f.format_category === "spreadsheet" ||
    ["xlsx", "xls", "csv", "tsv", "ods"].includes(
      (f.detection_format_id || f.actual_extension || f.claimed_extension || "").toLowerCase()
    );

  const isImage = (f: FileRecordSummary) =>
    f.format_category === "image" ||
    ["png", "jpeg", "jpg", "webp", "tiff", "bmp", "gif"].includes(
      (f.detection_format_id || f.actual_extension || f.claimed_extension || "").toLowerCase()
    );

  const isPresentation = (f: FileRecordSummary) =>
    f.format_category === "presentation" ||
    ["pptx", "ppt", "odp"].includes(
      (f.detection_format_id || f.actual_extension || f.claimed_extension || "").toLowerCase()
    );

  const handleInspect = (file: FileRecordSummary) => {
    setInspectingFile(file);
    if (isSpreadsheet(file)) {
      setModalTab("spreadsheet_intelligence");
    } else if (isImage(file)) {
      setModalTab("image_intelligence");
    } else if (isPresentation(file)) {
      setModalTab("presentation_intelligence");
    } else {
      setModalTab("extraction");
    }
  };

  return (
    <PageContainer
      title="File Library & Format Registry"
      subtitle="Catalog of evaluated files, multi-signal detection records, and registered format definitions"
    >
      {/* Navigation Tabs */}
      <div className="flex items-center gap-3 border-b border-border pb-3 mb-6">
        <button
          onClick={() => setActiveTab("files")}
          className={`flex items-center gap-2 pb-1 text-sm font-semibold transition border-b-2 -mb-[13px] ${
            activeTab === "files"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Files className="h-4 w-4" />
          Ingested Files ({files?.length ?? 0})
        </button>
        <button
          onClick={() => setActiveTab("registry")}
          className={`flex items-center gap-2 pb-1 text-sm font-semibold transition border-b-2 -mb-[13px] ${
            activeTab === "registry"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <BookOpen className="h-4 w-4" />
          Supported Formats Registry ({formatRegistry?.total_formats ?? 0})
        </button>
      </div>

      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={
              activeTab === "files"
                ? "Search files by name, hash, MIME, or detected format..."
                : "Search registered formats by name, category, or extension..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-border bg-card pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 sm:pb-0">
          <Filter className="h-4 w-4 text-muted-foreground shrink-0 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`rounded-lg px-2.5 py-1.5 text-xs capitalize font-medium transition shrink-0 ${
                selectedCategory === cat
                  ? "bg-primary text-white"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: Ingested Files Library */}
      {activeTab === "files" && (
        <div className="mt-6 rounded-xl border border-border bg-card p-5">
          {filesLoading ? (
            <LoadingState message="Loading cataloged files..." />
          ) : filesError ? (
            <ErrorState
              title="Failed to load file library"
              message={filesError instanceof Error ? filesError.message : "Unknown error"}
              onRetry={() => refetchFiles()}
            />
          ) : filteredFiles.length === 0 ? (
            <EmptyState
              icon={<Files className="h-8 w-8" />}
              title="No Files Found"
              description="No files match your current filters. Upload or detect files from the Upload gateway."
            />
          ) : (
            <div className="divide-y divide-border">
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-muted/30 px-3 rounded-lg transition"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-muted text-muted-foreground shrink-0 mt-0.5">
                      {getCategoryIcon(file.format_category)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium text-foreground truncate max-w-sm">
                          {file.original_filename}
                        </p>
                        <span className="text-[11px] text-muted-foreground">
                          ({formatBytes(file.file_size)})
                        </span>

                        {file.detection_format_id && (
                          <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                            {file.detection_format_id.toUpperCase()}
                          </span>
                        )}

                        {file.detected_mime_type && (
                          <span className="rounded bg-muted px-2 py-0.5 text-[11px] font-mono text-muted-foreground">
                            {file.detected_mime_type}
                          </span>
                        )}

                        {file.confidence_score !== undefined && (
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-medium ${
                              file.confidence_level === "high"
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            }`}
                          >
                            {Math.round(file.confidence_score * 100)}% Confidence
                          </span>
                        )}
                      </div>

                      {file.is_mismatch && (
                        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400 font-semibold">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          Extension Mismatch: Claimed .{file.claimed_extension}, actually .
                          {file.actual_extension}
                        </div>
                      )}

                      <div className="mt-1 flex items-center gap-3 text-[11px] text-muted-foreground font-mono">
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {file.sha256.slice(0, 16)}...
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(file.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                    <button
                      onClick={() => handleInspect(file)}
                      className="rounded border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition flex items-center gap-1"
                    >
                      <Info className="h-3.5 w-3.5" />
                      Inspect Record
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Supported Formats Registry */}
      {activeTab === "registry" && (
        <div className="mt-6 rounded-xl border border-border bg-card p-5">
          {registryLoading ? (
            <LoadingState message="Loading format registry..." />
          ) : registryError ? (
            <ErrorState
              title="Failed to load format registry"
              message={registryError instanceof Error ? registryError.message : "Unknown error"}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {(formatRegistry?.formats || []).map((fmt: FormatDetailData) => (
                <div
                  key={fmt.format_id}
                  className="rounded-lg border border-border bg-background p-3.5 hover:border-primary/50 transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(fmt.category)}
                        <h4 className="font-semibold text-xs text-foreground">
                          {fmt.display_name}
                        </h4>
                      </div>
                      <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-mono text-primary">
                        {fmt.format_id}
                      </span>
                    </div>

                    <p className="mt-1 text-[11px] text-muted-foreground line-clamp-2">
                      {fmt.description}
                    </p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-border/50 text-[10px] space-y-1">
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span>Category:</span>
                      <span className="font-medium capitalize text-foreground">{fmt.category}</span>
                    </div>
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span>Extensions:</span>
                      <span className="font-mono text-foreground">
                        {fmt.extensions.map((e) => `.${e}`).join(", ")}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span>Support Status:</span>
                      <span className="font-semibold uppercase text-emerald-600 dark:text-emerald-400">
                        {fmt.support_status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* File Record Inspection & Extraction Modal */}
      {inspectingFile && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="rounded-xl border border-border bg-card w-full max-w-6xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <FileBox className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold text-foreground text-sm truncate max-w-xs">
                    {inspectingFile.original_filename}
                  </h3>
                </div>
                <div className="flex items-center rounded-lg bg-muted p-0.5 text-xs">
                  {isSpreadsheet(inspectingFile) && (
                    <button
                      onClick={() => setModalTab("spreadsheet_intelligence")}
                      className={`px-3 py-1 rounded-md font-medium transition ${
                        modalTab === "spreadsheet_intelligence"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Spreadsheet Intelligence
                    </button>
                  )}
                  {isImage(inspectingFile) && (
                    <button
                      onClick={() => setModalTab("image_intelligence")}
                      className={`px-3 py-1 rounded-md font-medium transition ${
                        modalTab === "image_intelligence"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Image Intelligence
                    </button>
                  )}
                  {isPresentation(inspectingFile) && (
                    <button
                      onClick={() => setModalTab("presentation_intelligence")}
                      className={`px-3 py-1 rounded-md font-medium transition ${
                        modalTab === "presentation_intelligence"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Presentation Intelligence
                    </button>
                  )}
                  {!isSpreadsheet(inspectingFile) && !isImage(inspectingFile) && !isPresentation(inspectingFile) && (
                    <button
                      onClick={() => setModalTab("extraction")}
                      className={`px-3 py-1 rounded-md font-medium transition ${
                        modalTab === "extraction"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Document Content
                    </button>
                  )}
                  <button
                    onClick={() => setModalTab("detection")}
                    className={`px-3 py-1 rounded-md font-medium transition ${
                      modalTab === "detection"
                        ? "bg-card text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    Detection Provenance
                  </button>
                </div>
              </div>
              <button
                onClick={() => setInspectingFile(null)}
                className="text-muted-foreground hover:text-foreground transition p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {modalTab === "spreadsheet_intelligence" ? (
              <SpreadsheetIntelligenceView
                fileId={inspectingFile.id}
                filename={inspectingFile.original_filename}
                format={inspectingFile.detection_format_id || inspectingFile.actual_extension}
              />
            ) : modalTab === "extraction" ? (
              <DocumentExtractionView
                fileId={inspectingFile.id}
                filename={inspectingFile.original_filename}
                formatId={inspectingFile.detection_format_id || inspectingFile.extension}
                onClose={() => setInspectingFile(null)}
              />
            ) : modalTab === "presentation_intelligence" ? (
              <PresentationIntelligenceView
                fileId={inspectingFile.id}
                filename={inspectingFile.original_filename}
                format={inspectingFile.detection_format_id || inspectingFile.actual_extension}
              />
            ) : modalTab === "image_intelligence" ? (
              <ImageIntelligenceView
                fileId={inspectingFile.id}
                filename={inspectingFile.original_filename}
                format={inspectingFile.detection_format_id || inspectingFile.extension}
              />
            ) : (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 rounded-lg bg-background border border-border/60">
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Filename:</span>
                    <span className="font-medium text-foreground">{inspectingFile.original_filename}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">File ID:</span>
                    <span className="font-mono text-[10px] text-foreground">{inspectingFile.id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Detected MIME:</span>
                    <span className="font-mono text-foreground">
                      {inspectingFile.detected_mime_type || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Format & Category:</span>
                    <span className="font-medium capitalize text-foreground">
                      {inspectingFile.detection_format_id || "unknown"} (
                      {inspectingFile.format_category || "unknown"})
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">SHA-256 Checksum:</span>
                    <span className="font-mono text-[10px] truncate block text-foreground">
                      {inspectingFile.sha256}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[11px]">Detection Engine:</span>
                    <span className="text-foreground">
                      v{inspectingFile.detection_engine_version || "2.0.0"}
                    </span>
                  </div>
                </div>

                {/* Evidence Log */}
                {inspectingFile.detection_evidence && inspectingFile.detection_evidence.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                      Detection Evidence Log
                    </h4>
                    <div className="space-y-1.5">
                      {inspectingFile.detection_evidence.map((ev, i) => (
                        <div
                          key={i}
                          className="rounded bg-background p-2 border border-border/40 text-[11px] flex items-center justify-between"
                        >
                          <span className="font-semibold uppercase text-foreground">{ev.signal}</span>
                          <span className="font-mono text-[10px] text-muted-foreground">
                            {ev.details}
                          </span>
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                            {Math.round(ev.confidence_score * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {inspectingFile.file_metadata && Object.keys(inspectingFile.file_metadata).length > 0 && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-1.5">Extracted Header Metadata:</h4>
                    <pre className="bg-background rounded p-2 text-[10px] font-mono text-muted-foreground overflow-x-auto max-h-36">
                      {JSON.stringify(inspectingFile.file_metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
};
