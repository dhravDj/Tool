import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Download,
  Eye,
  Trash2,
  RefreshCw,
  Copy,
  Check,
  X,
  FileCode,
  Image as ImageIcon,
  Table as TableIcon,
  Archive,
  Layers,
} from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { ConversionRecordDTO } from "@/types/api";

interface QueuedFile {
  id: string;
  file: File;
  format: string;
  isImage: boolean;
  status: "queued" | "converting" | "completed" | "failed";
  progress: number;
  result?: ConversionRecordDTO;
  error?: string;
}

export const ConvertPage: React.FC = () => {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Target format: "txt" | "md"
  const [targetFormat, setTargetFormat] = useState<"txt" | "md">("md");
  const [convertBoth, setConvertBoth] = useState<boolean>(false);
  const [ocrEnabled, setOcrEnabled] = useState<boolean>(true);

  // Queue of files to convert
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Preview modal state
  const [previewResult, setPreviewResult] = useState<ConversionRecordDTO | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const isImageFile = (ext: string): boolean => {
    return ["png", "jpg", "jpeg", "webp", "tiff", "bmp", "svg"].includes(ext);
  };

  const addFilesToQueue = (newFiles: FileList | File[]) => {
    const additions: QueuedFile[] = [];
    for (let i = 0; i < newFiles.length; i++) {
      const f = newFiles[i];
      const ext = f.name.split(".").pop()?.toLowerCase() || "bin";
      additions.push({
        id: `${f.name}-${Date.now()}-${Math.random()}`,
        file: f,
        format: ext,
        isImage: isImageFile(ext),
        status: "queued",
        progress: 0,
      });
    }
    setQueue((prev) => [...prev, ...additions]);
    showToast({
      type: "info",
      title: "Files Added",
      message: `${additions.length} file(s) staged for conversion.`,
    });
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToQueue(e.target.files);
    }
    // reset input
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const clearQueue = () => {
    if (isProcessing) return;
    setQueue([]);
  };

  // Convert a single file
  const convertSingleFile = async (
    item: QueuedFile,
    fmt: "txt" | "md"
  ): Promise<ConversionRecordDTO> => {
    const formData = new FormData();
    formData.append("file", item.file);
    formData.append("target_format", fmt);
    formData.append("extraction_mode", fmt === "txt" ? "plain_text" : "structured_text");
    formData.append("ocr_enabled", String(ocrEnabled));

    return await api.convertFile(formData);
  };

  // Execute bulk conversion
  const handleConvertAll = async () => {
    if (queue.length === 0) {
      showToast({ type: "warning", title: "Empty Queue", message: "Please add files to convert." });
      return;
    }

    setIsProcessing(true);
    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];
      if (item.status === "completed") {
        successCount++;
        continue;
      }

      // Mark converting
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, status: "converting", progress: 40 } : q))
      );

      try {
        const result = await convertSingleFile(item, targetFormat);

        // If also convertBoth is checked, convert secondary format in background
        if (convertBoth) {
          const secondaryFormat = targetFormat === "md" ? "txt" : "md";
          try {
            await convertSingleFile(item, secondaryFormat);
          } catch {
            // secondary conversion optional
          }
        }

        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id ? { ...q, status: "completed", progress: 100, result } : q
          )
        );
        successCount++;
      } catch (err: unknown) {
        failCount++;
        const errMsg = err instanceof Error ? err.message : "Conversion failed";
        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id ? { ...q, status: "failed", progress: 100, error: errMsg } : q
          )
        );
      }
    }

    setIsProcessing(false);
    if (failCount === 0) {
      showToast({
        type: "success",
        title: "Bulk Conversion Complete",
        message: `Successfully converted ${successCount} file(s) to ${targetFormat.toUpperCase()}.`,
      });
    } else {
      showToast({
        type: "warning",
        title: "Batch Finished with Errors",
        message: `${successCount} succeeded, ${failCount} failed.`,
      });
    }
  };

  // Download all completed as single ZIP
  const handleDownloadAllZip = async () => {
    const completedIds = queue
      .map((q) => q.result?.id)
      .filter((id): id is string => Boolean(id));

    if (completedIds.length === 0) {
      showToast({
        type: "warning",
        title: "Nothing to download",
        message: "No successfully converted files yet.",
      });
      return;
    }

    try {
      showToast({
        type: "info",
        title: "Preparing ZIP",
        message: "Packaging converted files into a ZIP archive...",
      });
      const blob = await api.downloadBatchZip(completedIds);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `converted_files_${targetFormat}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showToast({
        type: "success",
        title: "Download Started",
        message: "Your ZIP package is downloading.",
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "ZIP download failed";
      showToast({ type: "error", title: "Download Failed", message: msg });
    }
  };

  const handleCopyPreview = () => {
    if (!previewResult?.preview_content) return;
    navigator.clipboard.writeText(previewResult.preview_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showToast({ type: "success", title: "Copied", message: "Content copied to clipboard." });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getFormatIcon = (ext: string, isImage: boolean) => {
    if (isImage) return <ImageIcon className="h-4 w-4 text-amber-500" />;
    if (["xlsx", "xls", "csv", "tsv", "ods"].includes(ext))
      return <TableIcon className="h-4 w-4 text-emerald-500" />;
    if (["py", "js", "ts", "jsx", "tsx", "c", "cpp", "go", "rs", "sql"].includes(ext))
      return <FileCode className="h-4 w-4 text-indigo-500" />;
    if (["zip", "tar", "gz", "7z"].includes(ext))
      return <Archive className="h-4 w-4 text-purple-500" />;
    return <FileText className="h-4 w-4 text-blue-500" />;
  };

  const completedCount = queue.filter((q) => q.status === "completed").length;

  return (
    <PageContainer
      title="Universal Bulk Converter"
      subtitle="Convert any files directly to clean Plain Text (.txt) or Markdown (.md), with built-in high-accuracy OCR image scanning."
    >
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Controls Card: Target Format & OCR Settings */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-6">
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-2">
                Target Output Format
              </label>
              <div className="inline-flex rounded-lg border border-border bg-muted/30 p-1">
                <button
                  type="button"
                  onClick={() => setTargetFormat("md")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    targetFormat === "md"
                      ? "bg-primary text-white shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <FileText className="h-4 w-4" />
                  Markdown (.md)
                </button>
                <button
                  type="button"
                  onClick={() => setTargetFormat("txt")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    targetFormat === "txt"
                      ? "bg-primary text-white shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <FileText className="h-4 w-4" />
                  Plain Text (.txt)
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-2 pt-4 sm:pt-0">
              <label className="flex items-center gap-2 cursor-pointer text-sm font-medium select-none">
                <input
                  type="checkbox"
                  checked={convertBoth}
                  onChange={(e) => setConvertBoth(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                />
                <span>Also generate complementary format (Both TXT & MD)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-sm font-medium select-none text-emerald-600 dark:text-emerald-400">
                <input
                  type="checkbox"
                  checked={ocrEnabled}
                  onChange={(e) => setOcrEnabled(e.target.checked)}
                  className="rounded border-border text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                />
                <span>📷 Enable Image Scan & OCR (Scans text from PNG, JPG, WEBP, Scanned PDF)</span>
              </label>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            {completedCount > 0 && (
              <Button
                variant="outline"
                onClick={handleDownloadAllZip}
                leftIcon={<Download className="h-4 w-4 text-emerald-500" />}
              >
                Download All ({completedCount}) as ZIP
              </Button>
            )}
            {queue.length > 0 && (
              <Button
                variant="primary"
                onClick={handleConvertAll}
                disabled={isProcessing}
                isLoading={isProcessing}
                leftIcon={<RefreshCw className="h-4 w-4" />}
              >
                Convert All Files ({queue.length})
              </Button>
            )}
          </div>
        </div>

        {/* Drag & Drop Bulk Ingestion Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-primary bg-primary/5 scale-[1.005]"
              : "border-border hover:border-primary/50 hover:bg-muted/30"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <UploadCloud className="h-7 w-7" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground">
                Drag and drop files here, or click to browse
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Upload multiple files at once. Supports all document types, spreadsheets, code, and images for OCR.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Badge variant="primary" size="sm">PDF, DOCX, DOC</Badge>
              <Badge variant="success" size="sm">XLSX, CSV, ODS</Badge>
              <Badge variant="warning" size="sm">📷 PNG, JPG, WEBP (OCR Scan)</Badge>
              <Badge variant="purple" size="sm">PPTX, Keynotes</Badge>
              <Badge variant="outline" size="sm">Code & Structured Data</Badge>
              <Badge variant="default" size="sm">ZIP, Archives</Badge>
            </div>
          </div>
        </div>

        {/* Bulk Queue Table */}
        {queue.length > 0 && (
          <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-3">
                <Layers className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-foreground">
                  Bulk Conversion Queue ({queue.length} files)
                </h3>
                {completedCount > 0 && (
                  <Badge variant="success" size="sm">
                    {completedCount} of {queue.length} ready
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearQueue}
                  disabled={isProcessing}
                  leftIcon={<Trash2 className="h-3.5 w-3.5 text-muted-foreground" />}
                >
                  Clear Queue
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isProcessing}
                >
                  + Add More Files
                </Button>
              </div>
            </div>

            <div className="divide-y divide-border">
              {queue.map((item, idx) => (
                <div
                  key={item.id}
                  className="px-5 py-3.5 flex flex-wrap sm:flex-nowrap items-center justify-between gap-4 hover:bg-muted/10 transition-colors"
                >
                  {/* File Info */}
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="text-xs font-mono text-muted-foreground w-6 text-right">
                      {idx + 1}.
                    </span>
                    <div className="p-2 rounded-lg bg-muted/50 shrink-0">
                      {getFormatIcon(item.format, item.isImage)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-foreground truncate block">
                          {item.file.name}
                        </span>
                        {item.isImage && (
                          <Badge variant="warning" size="sm" className="shrink-0 text-[10px]">
                            📷 OCR Scan
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span>{formatFileSize(item.file.size)}</span>
                        <span>•</span>
                        <span className="uppercase font-mono">{item.format}</span>
                        <span>→</span>
                        <span className="uppercase font-semibold text-primary">
                          {targetFormat}
                        </span>
                        {item.result && (
                          <>
                            <span>•</span>
                            <span className="text-emerald-600 dark:text-emerald-400">
                              {item.result.duration_seconds}s
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center gap-3 shrink-0">
                    {item.status === "queued" && (
                      <Badge variant="default" size="sm">
                        Queued
                      </Badge>
                    )}
                    {item.status === "converting" && (
                      <Badge variant="primary" size="sm" className="animate-pulse">
                        <RefreshCw className="h-3 w-3 animate-spin mr-1.5" />
                        Converting...
                      </Badge>
                    )}
                    {item.status === "completed" && item.result && (
                      <div className="flex items-center gap-2">
                        <Badge variant="success" size="sm">
                          <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                          Ready ({formatFileSize(item.result.output_size_bytes)})
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setPreviewResult(item.result || null)}
                          title="Preview Extracted Content"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <a
                          href={api.getConversionDownloadUrl(item.result.id)}
                          download={item.result.output_filename}
                          className="inline-flex items-center justify-center p-2 rounded-md hover:bg-muted text-primary transition-colors"
                          title="Download Converted File"
                        >
                          <Download className="h-4 w-4" />
                        </a>
                      </div>
                    )}
                    {item.status === "failed" && (
                      <div className="flex items-center gap-2">
                        <Badge variant="danger" size="sm" title={item.error}>
                          <AlertCircle className="h-3.5 w-3.5 mr-1" />
                          Failed
                        </Badge>
                      </div>
                    )}

                    {!isProcessing && item.status !== "converting" && (
                      <button
                        type="button"
                        onClick={() => removeFile(item.id)}
                        className="text-muted-foreground hover:text-red-500 p-1 rounded-md transition-colors"
                        title="Remove"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Bottom converted bulk bar */}
            {completedCount > 0 && (
              <div className="px-5 py-3.5 bg-emerald-500/5 border-t border-emerald-500/20 flex flex-wrap items-center justify-between gap-4">
                <span className="text-sm font-medium text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  {completedCount} file(s) converted successfully to .{targetFormat}
                </span>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleDownloadAllZip}
                  leftIcon={<Download className="h-4 w-4" />}
                >
                  Download All ({completedCount}) as ZIP
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Full Inline Preview Modal */}
        {previewResult && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
            <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in-50 zoom-in-95">
              {/* Modal Header */}
              <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground text-sm sm:text-base">
                      {previewResult.output_filename}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Source: {previewResult.original_filename} ({previewResult.source_format.toUpperCase()}) • Duration: {previewResult.duration_seconds}s
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyPreview}
                    leftIcon={copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                  >
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  <a
                    href={api.getConversionDownloadUrl(previewResult.id)}
                    download={previewResult.output_filename}
                    className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-all shadow-xs"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download
                  </a>
                  <button
                    type="button"
                    onClick={() => setPreviewResult(null)}
                    className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div className="p-5 overflow-y-auto flex-1 bg-muted/10 font-mono text-xs leading-relaxed text-foreground select-text whitespace-pre-wrap break-words">
                {previewResult.preview_content || "(No extracted text available for this file)"}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
