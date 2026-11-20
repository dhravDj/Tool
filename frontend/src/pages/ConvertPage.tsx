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
  Globe,
  GraduationCap,
  Sliders,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BookOpen,
  Zap,
} from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { ConversionRecordDTO } from "@/types/api";

type InputTab = "files" | "url" | "doi";
type OutputFormat = "md" | "txt" | "json" | "all";

interface QueuedItem {
  id: string;
  kind: "file" | "url" | "doi";
  file?: File;
  inputUrl?: string;
  inputDoi?: string;
  name: string;
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

  // Active input tab
  const [activeTab, setActiveTab] = useState<InputTab>("files");

  // URL & DOI text inputs
  const [urlInput, setUrlInput] = useState<string>("");
  const [doiInput, setDoiInput] = useState<string>("");

  // Target format: "md" | "txt" | "json" | "all"
  const [targetFormat, setTargetFormat] = useState<OutputFormat>("md");

  // Advanced Options Drawer
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [ocrEnabled, setOcrEnabled] = useState<boolean>(true);
  const [ocrTier, setOcrTier] = useState<string>("high");
  const [ocrMode, setOcrMode] = useState<string>("auto");
  const [ocrLang, setOcrLang] = useState<string>("en");
  const [enableChunking, setEnableChunking] = useState<boolean>(true);
  const [chunkSize, setChunkSize] = useState<number>(700);
  const [chunkOverlap, setChunkOverlap] = useState<number>(100);

  // Queue state
  const [queue, setQueue] = useState<QueuedItem[]>([]);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Preview modal state
  const [previewResult, setPreviewResult] = useState<ConversionRecordDTO | null>(null);
  const [previewTab, setPreviewTab] = useState<"md" | "txt" | "json">("md");
  const [copied, setCopied] = useState<boolean>(false);

  const isImageFormat = (ext: string): boolean => {
    return ["png", "jpg", "jpeg", "webp", "tiff", "bmp", "svg", "heic", "avif"].includes(ext);
  };

  const getFormatIcon = (format: string, kind: "file" | "url" | "doi") => {
    if (kind === "url") return <Globe className="h-5 w-5 text-sky-500" />;
    if (kind === "doi") return <GraduationCap className="h-5 w-5 text-amber-500" />;

    const f = format.toLowerCase();
    if (["xlsx", "xls", "csv", "tsv", "ods"].includes(f)) {
      return <TableIcon className="h-5 w-5 text-emerald-500" />;
    }
    if (["pptx", "ppt", "odp"].includes(f)) {
      return <Layers className="h-5 w-5 text-orange-500" />;
    }
    if (["png", "jpg", "jpeg", "webp", "tiff", "bmp", "svg"].includes(f)) {
      return <ImageIcon className="h-5 w-5 text-purple-500" />;
    }
    if (["zip", "tar", "gz", "7z", "bz2"].includes(f)) {
      return <Archive className="h-5 w-5 text-yellow-500" />;
    }
    if (["py", "js", "ts", "jsx", "tsx", "html", "css", "java", "sql", "json", "yaml"].includes(f)) {
      return <FileCode className="h-5 w-5 text-indigo-500" />;
    }
    if (f === "epub") {
      return <BookOpen className="h-5 w-5 text-teal-500" />;
    }
    return <FileText className="h-5 w-5 text-primary" />;
  };

  // Add files to queue
  const addFilesToQueue = (newFiles: FileList | File[]) => {
    const additions: QueuedItem[] = [];
    for (let i = 0; i < newFiles.length; i++) {
      const f = newFiles[i];
      const ext = f.name.split(".").pop()?.toLowerCase() || "bin";
      additions.push({
        id: `${f.name}-${Date.now()}-${Math.random()}`,
        kind: "file",
        file: f,
        name: f.name,
        format: ext,
        isImage: isImageFormat(ext),
        status: "queued",
        progress: 0,
      });
    }
    setQueue((prev) => [...prev, ...additions]);
    showToast({
      type: "info",
      title: "Files Added",
      message: `${additions.length} file(s) staged for universal conversion.`,
    });
  };

  // Add Webpage URL to queue
  const handleAddUrl = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanUrl = urlInput.trim();
    if (!cleanUrl) return;

    if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
      showToast({
        type: "error",
        title: "Invalid URL",
        message: "URL must start with http:// or https://",
      });
      return;
    }

    let domain = "webpage";
    try {
      domain = new URL(cleanUrl).hostname;
    } catch {
      // ignore
    }

    const newItem: QueuedItem = {
      id: `url-${Date.now()}-${Math.random()}`,
      kind: "url",
      inputUrl: cleanUrl,
      name: `${domain} (${cleanUrl.slice(0, 32)}...)`,
      format: "webpage",
      isImage: false,
      status: "queued",
      progress: 0,
    };

    setQueue((prev) => [...prev, newItem]);
    setUrlInput("");
    showToast({
      type: "info",
      title: "Webpage Staged",
      message: `Added live URL: ${cleanUrl}`,
    });
  };

  // Add Academic DOI to queue
  const handleAddDoi = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanDoi = doiInput.trim();
    if (!cleanDoi) return;

    const newItem: QueuedItem = {
      id: `doi-${Date.now()}-${Math.random()}`,
      kind: "doi",
      inputDoi: cleanDoi,
      name: `DOI: ${cleanDoi}`,
      format: "doi",
      isImage: false,
      status: "queued",
      progress: 0,
    };

    setQueue((prev) => [...prev, newItem]);
    setDoiInput("");
    showToast({
      type: "info",
      title: "DOI Staged",
      message: `Added academic paper DOI: ${cleanDoi}`,
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
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const removeItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const clearQueue = () => {
    if (isProcessing) return;
    setQueue([]);
  };

  // Process all queued items
  const handleConvertAll = async () => {
    const pendingItems = queue.filter((i) => i.status === "queued" || i.status === "failed");
    if (pendingItems.length === 0) {
      showToast({
        type: "warning",
        title: "Queue Empty",
        message: "Please add files, a webpage URL, or a DOI first.",
      });
      return;
    }

    setIsProcessing(true);
    let successCount = 0;
    let failCount = 0;

    for (const item of pendingItems) {
      setQueue((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: "converting", progress: 25 } : i))
      );

      try {
        let res: ConversionRecordDTO;

        if (item.kind === "file" && item.file) {
          const formData = new FormData();
          formData.append("file", item.file);
          formData.append("target_format", targetFormat === "all" ? "zip" : targetFormat);
          formData.append("extraction_mode", targetFormat === "all" ? "complete" : "structured_text");
          formData.append("ocr_enabled", String(ocrEnabled));
          formData.append("ocr_tier", ocrTier);
          formData.append("ocr_mode", ocrMode);
          formData.append("ocr_lang", ocrLang);
          formData.append("enable_chunking", String(enableChunking));
          formData.append("chunk_size", String(chunkSize));
          formData.append("chunk_overlap", String(chunkOverlap));
          formData.append("preserve_tables", "true");
          formData.append("preserve_headings", "true");

          res = await api.convertFile(formData);
        } else if (item.kind === "url" && item.inputUrl) {
          res = await api.convertUrl({
            url: item.inputUrl,
            target_format: targetFormat === "all" ? "zip" : targetFormat,
            extraction_mode: targetFormat === "all" ? "complete" : "structured_text",
          });
        } else if (item.kind === "doi" && item.inputDoi) {
          res = await api.convertDoi({
            doi: item.inputDoi,
            target_format: targetFormat === "all" ? "zip" : targetFormat,
            extraction_mode: targetFormat === "all" ? "complete" : "structured_text",
          });
        } else {
          throw new Error("Invalid queued item specification");
        }

        setQueue((prev) =>
          prev.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  status: "completed",
                  progress: 100,
                  result: res,
                  name: res.original_filename || i.name,
                }
              : i
          )
        );
        successCount++;
      } catch (err: unknown) {
        failCount++;
        const errMsg = err instanceof Error ? err.message : "Conversion execution failed";
        setQueue((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, status: "failed", progress: 100, error: errMsg } : i
          )
        );
      }
    }

    setIsProcessing(false);
    showToast({
      type: failCount > 0 ? "warning" : "success",
      title: "Batch Finished",
      message: `Completed: ${successCount} successful, ${failCount} failed.`,
    });
  };

  // Download all completed conversions in 1-Click ZIP
  const handleDownloadAllZip = async () => {
    const completedIds = queue
      .filter((i) => i.status === "completed" && i.result?.id)
      .map((i) => i.result!.id);

    if (completedIds.length === 0) {
      showToast({
        type: "warning",
        title: "No Completed Files",
        message: "No successfully converted files available to download.",
      });
      return;
    }

    try {
      showToast({
        type: "info",
        title: "Packaging ZIP",
        message: `Bundling ${completedIds.length} converted files...`,
      });
      const blob = await api.downloadBatchZip(completedIds);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `documind_conversions_${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast({
        type: "success",
        title: "Download Started",
        message: "Your conversion bundle ZIP has been downloaded.",
      });
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Batch ZIP download failed";
      showToast({
        type: "error",
        title: "Download Failed",
        message: errMsg,
      });
    }
  };

  const handleCopyPreview = () => {
    if (!previewResult?.preview_content) return;
    navigator.clipboard.writeText(previewResult.preview_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showToast({
      type: "success",
      title: "Copied",
      message: "Extracted content copied to clipboard.",
    });
  };

  const completedCount = queue.filter((i) => i.status === "completed").length;

  return (
    <PageContainer
      title="Universal File Converter & Content Extractor"
      subtitle="Universal Document Processor powered by high-speed deterministic extraction engines for Documents, Spreadsheets, Presentations, Images (OCR), Webpages, Academic DOIs, Code & Data."
    >
      <div className="space-y-6">
        {/* Supported Formats Banner */}
        <div className="flex flex-wrap items-center gap-1.5 p-3.5 bg-card/60 backdrop-blur-xs border border-border rounded-xl text-xs text-muted-foreground shadow-xs">
          <span className="font-semibold text-foreground flex items-center gap-1.5 mr-1">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Supported Formats:
          </span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">PDF</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">DOCX/DOC/ODT/RTF</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">XLSX/XLS/CSV/TSV</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">PPTX/PPT/ODP</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">EPUB</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">HTML/MHTML</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">PNG/JPG/WEBP/SVG (OCR)</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">Web URLs</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">Academic DOIs</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">JSON/YAML/XML</span>
          <span className="px-2 py-0.5 rounded-md bg-muted/60 font-mono text-[11px] text-foreground">Code (PY, JS, TS, SQL)</span>
        </div>

        {/* Input Mode Tabs & Target Output Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
            {/* Input Selection Tabs */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveTab("files")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === "files"
                    ? "bg-primary text-white shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                }`}
              >
                <UploadCloud className="h-4 w-4" />
                Upload Files & Folders
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("url")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === "url"
                    ? "bg-primary text-white shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                }`}
              >
                <Globe className="h-4 w-4" />
                Live Webpage URL
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("doi")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === "doi"
                    ? "bg-primary text-white shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                }`}
              >
                <GraduationCap className="h-4 w-4" />
                Academic Paper DOI
              </button>
            </div>

            {/* Target Output Format Pills */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mr-1">
                Output Format:
              </span>
              <div className="inline-flex rounded-lg border border-border p-1 bg-muted/30">
                <button
                  type="button"
                  onClick={() => setTargetFormat("md")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    targetFormat === "md"
                      ? "bg-primary text-white shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Markdown with YAML frontmatter, headers, tables & code blocks"
                >
                  Markdown (.md)
                </button>
                <button
                  type="button"
                  onClick={() => setTargetFormat("txt")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    targetFormat === "txt"
                      ? "bg-primary text-white shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Plain Text UTF-8 encoding with line breaks"
                >
                  Plain Text (.txt)
                </button>
                <button
                  type="button"
                  onClick={() => setTargetFormat("json")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    targetFormat === "json"
                      ? "bg-primary text-white shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Structured Document IR & Semantic RAG Chunks"
                >
                  JSON (.json)
                </button>
                <button
                  type="button"
                  onClick={() => setTargetFormat("all")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    targetFormat === "all"
                      ? "bg-primary text-white shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Generate All 3 Formats (.md, .txt, .json) simultaneously"
                >
                  All Formats (.zip)
                </button>
              </div>
            </div>
          </div>

          {/* Tab 1: Local Files Drag & Drop Dropzone */}
          {activeTab === "files" && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-primary bg-primary/5 scale-[0.99]"
                  : "border-border hover:border-primary/50 hover:bg-muted/20"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="hidden"
                onChange={handleFileSelect}
              />
              <div className="flex flex-col items-center justify-center gap-3">
                <div className="p-4 rounded-full bg-primary/10 text-primary">
                  <UploadCloud className="h-8 w-8 sm:h-10 sm:w-10" />
                </div>
                <div>
                  <p className="text-base font-semibold text-foreground">
                    Click to browse or drag and drop any files here
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    PDF, Word, Excel, PowerPoint, EPUB, Images, Code, Data, Text up to 500 MB & 50,000 pages
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Live Webpage URL Input */}
          {activeTab === "url" && (
            <form onSubmit={handleAddUrl} className="space-y-3">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                    <Globe className="h-4 w-4" />
                  </div>
                  <input
                    type="url"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="Enter article URL (e.g. https://en.wikipedia.org/wiki/Artificial_intelligence)"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
                <Button type="submit" leftIcon={<Globe className="h-4 w-4" />}>
                  Add Webpage
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Extracts clean article text, metadata, and tables without ads, navigation menus, or boilerplate.
              </p>
            </form>
          )}

          {/* Tab 3: Academic Paper DOI Input */}
          {activeTab === "doi" && (
            <form onSubmit={handleAddDoi} className="space-y-3">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                    <GraduationCap className="h-4 w-4" />
                  </div>
                  <input
                    type="text"
                    value={doiInput}
                    onChange={(e) => setDoiInput(e.target.value)}
                    placeholder="Enter academic DOI (e.g. 10.1038/s41586-020-2649-2 or https://doi.org/...)"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
                <Button type="submit" leftIcon={<GraduationCap className="h-4 w-4" />}>
                  Retrieve Paper
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Queries CrossRef, DataCite, Europe PMC, and Unpaywall to discover Open Access full-text JATS XML or PDF.
              </p>
            </form>
          )}

          {/* Advanced OCR & RAG Chunking Settings (Collapsible) */}
          <div className="border border-border/80 rounded-lg p-3 bg-muted/10">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full text-xs font-semibold text-foreground hover:text-primary transition-colors"
            >
              <div className="flex items-center gap-2">
                <Sliders className="h-3.5 w-3.5 text-primary" />
                <span>OCR Model Tier & Processing Configuration</span>
                <span className="text-[11px] font-normal text-muted-foreground">
                  (RapidOCR, Chunking, Language)
                </span>
              </div>
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showAdvanced && (
              <div className="space-y-4 mt-4 pt-3 border-t border-border">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* OCR Toggle */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={ocrEnabled}
                        onChange={(e) => setOcrEnabled(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary"
                      />
                      Enable OCR Scanning
                    </label>
                    <p className="text-[11px] text-muted-foreground">
                      Scans images & embedded diagrams in PDFs.
                    </p>
                  </div>

                  {/* OCR Model Tier */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground">OCR Model Tier</label>
                    <select
                      value={ocrTier}
                      onChange={(e) => setOcrTier(e.target.value)}
                      disabled={!ocrEnabled}
                      className="w-full text-xs px-2.5 py-1.5 rounded-md border border-border bg-background text-foreground disabled:opacity-50"
                    >
                      <option value="high">High (Maximum Precision)</option>
                      <option value="medium">Medium (Balanced)</option>
                      <option value="small">Small (Fast)</option>
                      <option value="tiny">Tiny (Lightweight)</option>
                    </select>
                  </div>

                  {/* OCR Mode */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground">OCR Mode</label>
                    <select
                      value={ocrMode}
                      onChange={(e) => setOcrMode(e.target.value)}
                      disabled={!ocrEnabled}
                      className="w-full text-xs px-2.5 py-1.5 rounded-md border border-border bg-background text-foreground disabled:opacity-50"
                    >
                      <option value="auto">Auto (Detect text density)</option>
                      <option value="ocr">Force OCR (All elements)</option>
                      <option value="native">Native Text Only (No OCR)</option>
                      <option value="math">Math & LaTeX Equations</option>
                    </select>
                  </div>

                  {/* OCR Language */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground">OCR Language</label>
                    <select
                      value={ocrLang}
                      onChange={(e) => setOcrLang(e.target.value)}
                      disabled={!ocrEnabled}
                      className="w-full text-xs px-2.5 py-1.5 rounded-md border border-border bg-background text-foreground disabled:opacity-50"
                    >
                      <option value="en">English (en)</option>
                      <option value="hi">Hindi (hi)</option>
                      <option value="fr">French (fr)</option>
                      <option value="de">German (de)</option>
                      <option value="es">Spanish (es)</option>
                      <option value="ch">Chinese (ch)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-border/50">
                  {/* Semantic RAG Chunking Toggle */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={enableChunking}
                        onChange={(e) => setEnableChunking(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary"
                      />
                      Semantic RAG Chunking
                    </label>
                    <p className="text-[11px] text-muted-foreground">
                      Segments document into semantic passages for embedding & vector search.
                    </p>
                  </div>

                  {/* Chunk Size */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground flex justify-between">
                      <span>Chunk Token Size</span>
                      <span className="text-muted-foreground">{chunkSize} tokens</span>
                    </label>
                    <input
                      type="number"
                      min={100}
                      max={4000}
                      step={50}
                      value={chunkSize}
                      onChange={(e) => setChunkSize(Number(e.target.value) || 700)}
                      disabled={!enableChunking}
                      className="w-full text-xs px-2.5 py-1.5 rounded-md border border-border bg-background text-foreground disabled:opacity-50"
                    />
                  </div>

                  {/* Chunk Overlap */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-foreground flex justify-between">
                      <span>Overlap Tokens</span>
                      <span className="text-muted-foreground">{chunkOverlap} tokens</span>
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={1000}
                      step={25}
                      value={chunkOverlap}
                      onChange={(e) => setChunkOverlap(Number(e.target.value) || 100)}
                      disabled={!enableChunking}
                      className="w-full text-xs px-2.5 py-1.5 rounded-md border border-border bg-background text-foreground disabled:opacity-50"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Conversion Queue Card */}
        {queue.length > 0 && (
          <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
            {/* Queue Header & Action Bar */}
            <div className="px-5 py-4 border-b border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-muted/20">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-foreground text-sm sm:text-base">
                  Conversion Queue ({queue.length})
                </h3>
                {completedCount > 0 && (
                  <Badge variant="success" size="sm">
                    {completedCount} Completed
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
                {/* 1-Click Batch Download ZIP Button */}
                {completedCount > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownloadAllZip}
                    leftIcon={<Download className="h-4 w-4 text-emerald-500" />}
                  >
                    Download All (ZIP)
                  </Button>
                )}

                {/* Convert All Button */}
                <Button
                  size="sm"
                  onClick={handleConvertAll}
                  isLoading={isProcessing}
                  leftIcon={isProcessing ? undefined : <Zap className="h-4 w-4" />}
                >
                  {isProcessing ? "Converting..." : "Convert All"}
                </Button>

                {/* Clear Queue */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearQueue}
                  disabled={isProcessing}
                  leftIcon={<Trash2 className="h-4 w-4" />}
                >
                  Clear
                </Button>
              </div>
            </div>

            {/* Queue Items List */}
            <div className="divide-y divide-border max-h-[60vh] overflow-y-auto">
              {queue.map((item) => (
                <div
                  key={item.id}
                  className="px-5 py-3.5 flex items-center justify-between gap-4 hover:bg-muted/10 transition-colors"
                >
                  {/* Left: Icon & Name */}
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="p-2 rounded-lg bg-muted/60 shrink-0">
                      {getFormatIcon(item.format, item.kind)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-foreground truncate max-w-xs sm:max-w-md">
                          {item.name}
                        </p>
                        <span className="uppercase text-[10px] font-mono px-1.5 py-0.5 rounded-sm bg-muted text-muted-foreground shrink-0">
                          {item.format}
                        </span>
                        {item.isImage && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-sm bg-purple-500/10 text-purple-600 dark:text-purple-400 shrink-0">
                            OCR
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        {item.file && <span>{(item.file.size / 1024).toFixed(1)} KB</span>}
                        {item.result && (
                          <>
                            <span className="text-emerald-500 font-medium">
                              Output: {item.result.output_filename}
                            </span>
                            <span>•</span>
                            <span>{item.result.duration_seconds}s</span>
                          </>
                        )}
                        {item.error && (
                          <span className="text-rose-500 truncate max-w-sm">{item.error}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Status & Actions */}
                  <div className="flex items-center gap-3 shrink-0">
                    {/* Status Indicators */}
                    {item.status === "queued" && (
                      <Badge variant="outline" size="sm">
                        Queued
                      </Badge>
                    )}
                    {item.status === "converting" && (
                      <div className="flex items-center gap-2 text-xs text-primary font-medium">
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Converting...</span>
                      </div>
                    )}
                    {item.status === "completed" && (
                      <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Done</span>
                      </div>
                    )}
                    {item.status === "failed" && (
                      <div className="flex items-center gap-1.5 text-xs text-rose-500 font-medium">
                        <AlertCircle className="h-4 w-4" />
                        <span>Failed</span>
                      </div>
                    )}

                    {/* Actions: Preview & Download */}
                    {item.status === "completed" && item.result && (
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            setPreviewResult(item.result || null);
                            setPreviewTab("md");
                          }}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                          title="Preview Extracted Content"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <a
                          href={api.getConversionDownloadUrl(item.result.id)}
                          download={item.result.output_filename}
                          className="p-1.5 rounded-md text-primary hover:bg-primary/10 transition-colors"
                          title="Download Converted File"
                        >
                          <Download className="h-4 w-4" />
                        </a>
                      </div>
                    )}

                    {/* Remove queued item */}
                    {!isProcessing && (
                      <button
                        type="button"
                        onClick={() => removeItem(item.id)}
                        className="p-1.5 rounded-md text-muted-foreground hover:text-rose-500 hover:bg-muted transition-colors"
                        title="Remove from queue"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Multi-Tab Inline Content Preview Modal */}
        {previewResult && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden animate-in fade-in-50 zoom-in-95">
              {/* Modal Header */}
              <div className="px-5 py-3.5 border-b border-border flex items-center justify-between bg-muted/20">
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

                {/* Actions */}
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
                    className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* View Tabs */}
              <div className="px-5 py-2 border-b border-border bg-muted/10 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPreviewTab("md")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    previewTab === "md"
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Rendered Text
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewTab("txt")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    previewTab === "txt"
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Raw Monospace
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewTab("json")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    previewTab === "json"
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Metadata & Details
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-5 overflow-y-auto flex-1 bg-muted/5 font-mono text-xs leading-relaxed text-foreground select-text whitespace-pre-wrap break-words">
                {previewTab === "json" ? (
                  <pre className="text-muted-foreground">
                    {JSON.stringify(
                      {
                        id: previewResult.id,
                        original_filename: previewResult.original_filename,
                        source_format: previewResult.source_format,
                        target_format: previewResult.target_format,
                        output_filename: previewResult.output_filename,
                        output_size_bytes: previewResult.output_size_bytes,
                        duration_seconds: previewResult.duration_seconds,
                        warnings: previewResult.warnings,
                        created_at: previewResult.created_at,
                        completed_at: previewResult.completed_at,
                      },
                      null,
                      2
                    )}
                  </pre>
                ) : (
                  previewResult.preview_content || "(No extracted text available for this file)"
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
