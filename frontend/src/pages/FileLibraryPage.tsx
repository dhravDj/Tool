import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  Download,
  FileBox,
  FileCode,
  Files,
  FileSpreadsheet,
  FileText,
  Filter,
  Grid,
  Hash,
  Image as ImageIcon,
  Info,
  LayoutList,
  MessageSquare,
  Music,
  Package,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Video,
} from "lucide-react";
import { UniversalFileInspector } from "@/components/inspector/UniversalFileInspector";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { FileRecordSummary, FormatDetailData } from "@/types/api";

export const FileLibraryPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState<"files" | "registry">("files");
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "name_asc" | "size_desc">("date_desc");

  // Selection & Actions
  const [inspectingFile, setInspectingFile] = useState<FileRecordSummary | null>(null);
  const [fileToDelete, setFileToDelete] = useState<FileRecordSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Queries
  const {
    data: files,
    isLoading: filesLoading,
    error: filesError,
    refetch: refetchFiles,
    isFetching,
  } = useQuery({
    queryKey: ["files"],
    queryFn: () => api.getFiles(100, 0),
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
  ];

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
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

  const handleDeleteFile = async () => {
    if (!fileToDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteFile(fileToDelete.id);
      success("File Deleted", `${fileToDelete.original_filename} was successfully removed.`);
      setFileToDelete(null);
      refetchFiles();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete file.";
      error("Deletion Failed", msg);
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredFiles = (files || [])
    .filter((f) => {
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        f.original_filename.toLowerCase().includes(term) ||
        f.sha256.toLowerCase().includes(term) ||
        (f.detected_mime_type && f.detected_mime_type.toLowerCase().includes(term)) ||
        (f.detection_format_id && f.detection_format_id.toLowerCase().includes(term));

      const matchesCat =
        selectedCategory === "all" ||
        f.format_category === selectedCategory ||
        (selectedCategory === "document" && f.format_category === "pdf");

      const matchesStatus =
        selectedStatus === "all" ||
        f.status === selectedStatus;

      return matchesSearch && matchesCat && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === "date_desc") {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      if (sortBy === "date_asc") {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }
      if (sortBy === "name_asc") {
        return a.original_filename.localeCompare(b.original_filename);
      }
      if (sortBy === "size_desc") {
        return b.file_size - a.file_size;
      }
      return 0;
    });

  return (
    <PageContainer
      title="File Library & Explorer"
      subtitle="Universal file catalog with deep inspection, multi-engine analysis, and AI Q&A"
      action={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchFiles()}
            isLoading={isFetching}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate("/upload")}
            leftIcon={<Plus className="h-3.5 w-3.5" />}
          >
            Upload Files
          </Button>
        </div>
      }
    >
      {/* Top Tab Bar */}
      <div className="flex items-center border-b border-border gap-6">
        <button
          onClick={() => setActiveTab("files")}
          className={`flex items-center gap-2 pb-3 text-xs font-semibold border-b-2 transition ${
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
          className={`flex items-center gap-2 pb-3 text-xs font-semibold border-b-2 transition ${
            activeTab === "registry"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <BookOpen className="h-4 w-4" />
          Supported Formats Registry ({formatRegistry?.total_formats ?? 0})
        </button>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col md:flex-row gap-3 mt-4 items-stretch md:items-center justify-between">
        <div className="relative flex-1 max-w-lg">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={
              activeTab === "files"
                ? "Search files by name, checksum, MIME, or extension..."
                : "Search registered formats by category or extension..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-border bg-card pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-primary shadow-2xs"
          />
        </div>

        {activeTab === "files" && (
          <div className="flex items-center gap-2 flex-wrap">
            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="text-xs px-2.5 py-2 rounded-xl border border-border bg-card text-foreground focus:outline-hidden shadow-2xs"
            >
              <option value="all">All Statuses</option>
              <option value="processed">Ready / Processed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-xs px-2.5 py-2 rounded-xl border border-border bg-card text-foreground focus:outline-hidden shadow-2xs"
            >
              <option value="date_desc">Newest Ingested</option>
              <option value="date_asc">Oldest Ingested</option>
              <option value="name_asc">Name (A-Z)</option>
              <option value="size_desc">File Size (Largest)</option>
            </select>

            {/* View Mode Toggle */}
            <div className="flex items-center rounded-xl bg-muted/60 p-1 border border-border shadow-2xs">
              <button
                onClick={() => setViewMode("list")}
                className={`p-1.5 rounded-lg transition ${
                  viewMode === "list" ? "bg-card text-foreground shadow-xs" : "text-muted-foreground"
                }`}
                title="List View"
                aria-label="List View"
              >
                <LayoutList className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={`p-1.5 rounded-lg transition ${
                  viewMode === "grid" ? "bg-card text-foreground shadow-xs" : "text-muted-foreground"
                }`}
                title="Grid View"
                aria-label="Grid View"
              >
                <Grid className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 mt-3">
        <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0 mr-1" />
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`rounded-lg px-2.5 py-1 text-xs capitalize font-medium transition shrink-0 ${
              selectedCategory === cat
                ? "bg-primary text-white shadow-2xs"
                : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Tab 1: Files Explorer */}
      {activeTab === "files" && (
        <div className="mt-4">
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
              title="No Files Matching Filters"
              description="Upload files from the Ingestion gateway or adjust your search criteria."
            />
          ) : viewMode === "list" ? (
            /* List View */
            <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-2xs divide-y divide-border/60">
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-muted/30 transition group"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="p-2.5 rounded-xl bg-muted text-muted-foreground shrink-0 mt-0.5">
                      {getCategoryIcon(file.format_category)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <button
                          onClick={() => setInspectingFile(file)}
                          className="text-xs font-semibold text-foreground hover:text-primary transition truncate max-w-sm sm:max-w-md text-left"
                        >
                          {file.original_filename}
                        </button>
                        <span className="text-[11px] text-muted-foreground font-mono">
                          ({formatBytes(file.file_size)})
                        </span>
                        {file.detection_format_id && (
                          <Badge variant="primary" size="sm">
                            {file.detection_format_id.toUpperCase()}
                          </Badge>
                        )}
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                            file.status === "processed"
                              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                              : file.status === "processing"
                                ? "bg-blue-500/10 text-blue-500"
                                : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {file.status}
                        </span>
                      </div>

                      {file.is_mismatch && (
                        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400 font-semibold">
                          <AlertTriangle className="h-3 w-3" />
                          Extension Mismatch: Claimed .{file.claimed_extension}, actually .{file.actual_extension}
                        </div>
                      )}

                      <div className="mt-1 flex items-center gap-3 text-[10px] text-muted-foreground font-mono">
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {file.sha256.slice(0, 12)}...
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(file.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setInspectingFile(file)}
                      leftIcon={<Info className="h-3.5 w-3.5" />}
                    >
                      Inspect
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/ai`)}
                      leftIcon={<MessageSquare className="h-3.5 w-3.5 text-blue-500" />}
                    >
                      Chat
                    </Button>

                    <a
                      href={api.getFileDownloadUrl(file.id)}
                      download={file.original_filename}
                      className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                      title="Download Original"
                    >
                      <Download className="h-4 w-4" />
                    </a>

                    <button
                      onClick={() => setFileToDelete(file)}
                      className="p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition"
                      title="Delete File"
                      aria-label="Delete File"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Grid View */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="rounded-2xl border border-border bg-card p-4 hover:border-primary/50 transition flex flex-col justify-between shadow-2xs space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="p-2 rounded-xl bg-muted text-muted-foreground">
                        {getCategoryIcon(file.format_category)}
                      </div>
                      <Badge variant="primary" size="sm">
                        {(file.detection_format_id || file.extension).toUpperCase()}
                      </Badge>
                    </div>

                    <div>
                      <h4
                        onClick={() => setInspectingFile(file)}
                        className="text-xs font-semibold text-foreground hover:text-primary transition truncate cursor-pointer"
                        title={file.original_filename}
                      >
                        {file.original_filename}
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {formatBytes(file.file_size)} • {file.format_category || "Document"}
                      </p>
                    </div>

                    <div className="text-[10px] text-muted-foreground font-mono truncate">
                      SHA: {file.sha256.slice(0, 16)}...
                    </div>
                  </div>

                  <div className="pt-3 border-t border-border/60 flex items-center justify-between">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                        file.status === "processed"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {file.status}
                    </span>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setInspectingFile(file)}
                      >
                        Inspect
                      </Button>
                      <button
                        onClick={() => setFileToDelete(file)}
                        className="p-1 rounded text-muted-foreground hover:text-red-500"
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Supported Formats Registry */}
      {activeTab === "registry" && (
        <div className="mt-4">
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
                  className="rounded-2xl border border-border bg-card p-4 hover:border-primary/50 transition flex flex-col justify-between shadow-2xs"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(fmt.category)}
                        <h4 className="font-semibold text-xs text-foreground">
                          {fmt.display_name}
                        </h4>
                      </div>
                      <Badge variant="primary" size="sm">
                        {fmt.format_id}
                      </Badge>
                    </div>

                    <p className="text-[11px] text-muted-foreground line-clamp-2">
                      {fmt.description}
                    </p>

                    <div className="pt-2 text-[10px] space-y-1 text-muted-foreground">
                      <div className="flex justify-between">
                        <span>Category:</span>
                        <span className="font-medium capitalize text-foreground">{fmt.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Extensions:</span>
                        <span className="font-mono text-foreground">
                          {fmt.extensions.map((e) => `.${e}`).join(", ")}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Support Status:</span>
                        <span className="font-semibold uppercase text-emerald-600 dark:text-emerald-400">
                          {fmt.support_status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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

      {/* Deletion Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(fileToDelete)}
        title="Confirm File Deletion"
        description={`Are you sure you want to permanently delete "${fileToDelete?.original_filename}"? This will remove the file record and its extracted metadata from storage.`}
        confirmLabel={isDeleting ? "Deleting..." : "Delete Permanently"}
        isDestructive={true}
        onConfirm={handleDeleteFile}
        onCancel={() => setFileToDelete(null)}
      />
    </PageContainer>
  );
};
