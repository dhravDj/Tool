import React, { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  UploadCloud,
  FileText,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Download,
  RefreshCw,
  ArrowRight,
  FileBox,
  Eye,
  FileCheck,
  CheckSquare,
  Square,
} from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { ConversionRecordDTO } from "@/types/api";

export const ConvertPage: React.FC = () => {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // States
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [detectedFormat, setDetectedFormat] = useState<string>("");
  const [extractionMode, setExtractionMode] = useState<"plain_text" | "structured_text" | "complete">("structured_text");
  const [targetFormat, setTargetFormat] = useState<string>("md");
  const [ocrEnabled, setOcrEnabled] = useState<boolean>(true);
  const [preserveTables, setPreserveTables] = useState<boolean>(true);
  const [preserveHeadings, setPreserveHeadings] = useState<boolean>(true);

  const [isConverting, setIsConverting] = useState<boolean>(false);
  const [conversionResult, setConversionResult] = useState<ConversionRecordDTO | null>(null);
  const [previewTab, setPreviewTab] = useState<"formatted" | "raw" | "files" | "meta">("formatted");
  const [bundleFiles, setBundleFiles] = useState<Array<{ filename: string; size_bytes: number }>>([]);

  // Fetch capabilities
  const { data: capabilities } = useQuery({
    queryKey: ["conversionCapabilities"],
    queryFn: api.getConversionCapabilities,
  });

  // When file changes, auto-detect format and set default target format
  useEffect(() => {
    if (!selectedFile) {
      setDetectedFormat("");
      return;
    }
    const ext = selectedFile.name.split(".").pop()?.toLowerCase() || "";
    setDetectedFormat(ext);

    // Pick sensible default target format based on input
    if (["xlsx", "xls", "csv", "tsv", "ods"].includes(ext)) {
      setTargetFormat("csv");
    } else if (["mp3", "wav", "m4a", "flac"].includes(ext)) {
      setTargetFormat("srt");
    } else if (["json", "xml", "yaml", "toml"].includes(ext)) {
      setTargetFormat("json");
    } else {
      setTargetFormat("md");
    }
  }, [selectedFile]);

  // When extraction mode changes, adapt target format
  const handleModeChange = (mode: "plain_text" | "structured_text" | "complete") => {
    setExtractionMode(mode);
    if (mode === "plain_text") {
      setTargetFormat("txt");
    } else if (mode === "structured_text") {
      setTargetFormat("md");
    } else if (mode === "complete") {
      setTargetFormat("zip");
    }
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      showToast({ type: "error", title: "No file selected", message: "Please select a file to convert." });
      return;
    }

    setIsConverting(true);
    setConversionResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("target_format", targetFormat);
      formData.append("extraction_mode", extractionMode);
      formData.append("ocr_enabled", String(ocrEnabled));
      formData.append("preserve_tables", String(preserveTables));
      formData.append("preserve_headings", String(preserveHeadings));

      const result = await api.convertFile(formData);
      setConversionResult(result);

      if (result.target_format === "zip") {
        const files = await api.getConversionFiles(result.id);
        setBundleFiles(files);
      }

      showToast({
        type: "success",
        title: "Conversion Completed",
        message: `Converted '${selectedFile.name}' to ${result.output_filename} in ${result.duration_seconds}s.`,
      });
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Conversion failed.";
      showToast({ type: "error", title: "Conversion Error", message: errMsg });
    } finally {
      setIsConverting(false);
    }
  };

  // Find allowed target formats for detected format
  const matchedCap = capabilities?.find(
    (c) => c.input_format.toLowerCase() === detectedFormat.toLowerCase()
  );
  const allowedOutputs = matchedCap?.allowed_output_formats || ["txt", "md", "json", "html", "zip"];

  return (
    <PageContainer
      title="Universal File Converter & Extractor"
      subtitle="Extract authentic content and convert across 60+ document, spreadsheet, media, and code formats."
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Configuration */}
        <div className="lg:col-span-5 space-y-6">
          {/* File Upload Area */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-blue-600" />
              1. Select Source File
            </h2>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 rounded-xl p-8 text-center cursor-pointer transition-colors bg-slate-50/50 dark:bg-slate-950/50"
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileSelect}
              />
              <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Drag and drop your file here, or <span className="text-blue-600 dark:text-blue-400">browse</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                PDF, Word, Excel, PowerPoint, Images, Audio, Video, Code, Archives up to 500MB
              </p>
            </div>

            {selectedFile && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileText className="w-6 h-6 text-blue-600 shrink-0" />
                  <div className="truncate">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Detected:{" "}
                      <span className="font-semibold text-blue-600 dark:text-blue-400 uppercase">
                        {detectedFormat}
                      </span>
                    </p>
                  </div>
                </div>
                <Badge variant="success" className="shrink-0 uppercase text-[10px]">
                  Ready
                </Badge>
              </div>
            )}
          </div>

          {/* Mode Selection */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              2. Select Extraction Mode
            </h2>

            <div className="space-y-3">
              {/* Mode A */}
              <div
                onClick={() => handleModeChange("plain_text")}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                  extractionMode === "plain_text"
                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 ring-1 ring-blue-500"
                    : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    Mode A: Plain Text (.txt)
                  </span>
                  <Badge variant={extractionMode === "plain_text" ? "primary" : "outline"} className="text-[10px]">
                    Fast
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Extract pure readable text. Strips unnecessary formatting for LLMs, search, or scripts.
                </p>
              </div>

              {/* Mode B */}
              <div
                onClick={() => handleModeChange("structured_text")}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                  extractionMode === "structured_text"
                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 ring-1 ring-blue-500"
                    : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    Mode B: Structured Text (.md)
                  </span>
                  <Badge variant={extractionMode === "structured_text" ? "primary" : "outline"} className="text-[10px]">
                    Recommended
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Preserve headings, tables, code fences, lists, and slide/sheet boundaries in GitHub Markdown.
                </p>
              </div>

              {/* Mode C */}
              <div
                onClick={() => handleModeChange("complete")}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                  extractionMode === "complete"
                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 ring-1 ring-blue-500"
                    : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    Mode C: Complete Extraction (.zip)
                  </span>
                  <Badge variant={extractionMode === "complete" ? "primary" : "outline"} className="text-[10px]">
                    Full Bundle
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Export full archive with .txt, .md, .json, .html, tables as individual .csv, and manifest.
                </p>
              </div>
            </div>
          </div>

          {/* Output Format Selection */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-emerald-600" />
              3. Target Output Format
            </h2>

            <div className="grid grid-cols-4 gap-2">
              {["txt", "md", "json", "csv", "html", "zip", "srt", "vtt"].map((fmt) => {
                const isAllowed = allowedOutputs.includes(fmt) || extractionMode === "complete";
                const isSelected = targetFormat === fmt;

                return (
                  <button
                    key={fmt}
                    type="button"
                    disabled={!isAllowed}
                    onClick={() => setTargetFormat(fmt)}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold uppercase transition-all ${
                      isSelected
                        ? "bg-blue-600 text-white shadow-sm"
                        : isAllowed
                        ? "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                        : "bg-slate-50 dark:bg-slate-950 text-slate-300 dark:text-slate-700 cursor-not-allowed border border-transparent"
                    }`}
                  >
                    .{fmt}
                  </button>
                );
              })}
            </div>

            {/* Extraction Options */}
            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 space-y-2">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Conversion Options</p>
              <div
                onClick={() => setOcrEnabled(!ocrEnabled)}
                className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none"
              >
                {ocrEnabled ? (
                  <CheckSquare className="w-4 h-4 text-blue-600" />
                ) : (
                  <Square className="w-4 h-4 text-slate-400" />
                )}
                <span>Enable Optical Character Recognition (OCR) for scanned images</span>
              </div>
              <div
                onClick={() => setPreserveTables(!preserveTables)}
                className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none"
              >
                {preserveTables ? (
                  <CheckSquare className="w-4 h-4 text-blue-600" />
                ) : (
                  <Square className="w-4 h-4 text-slate-400" />
                )}
                <span>Preserve tabular structures &amp; column alignments</span>
              </div>
              <div
                onClick={() => setPreserveHeadings(!preserveHeadings)}
                className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none"
              >
                {preserveHeadings ? (
                  <CheckSquare className="w-4 h-4 text-blue-600" />
                ) : (
                  <Square className="w-4 h-4 text-slate-400" />
                )}
                <span>Preserve section headings and document hierarchy</span>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <Button
            size="lg"
            className="w-full text-base font-medium py-3"
            disabled={!selectedFile || isConverting}
            onClick={handleConvert}
          >
            {isConverting ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                Converting File...
              </>
            ) : (
              <>
                Convert & Extract Content
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>
        </div>

        {/* Right Column: Output Preview & Results */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm min-h-[580px] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-slate-500" />
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                  Conversion Preview & Download
                </h3>
              </div>

              {conversionResult && (
                <div className="flex items-center gap-2">
                  <a
                    href={api.getConversionDownloadUrl(conversionResult.id)}
                    download={conversionResult.output_filename}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium transition-colors shadow-sm"
                  >
                    <Download className="w-4 h-4" />
                    Download {conversionResult.output_filename}
                  </a>
                </div>
              )}
            </div>

            {/* If no result yet */}
            {!conversionResult && !isConverting && (
              <div className="my-auto text-center py-12">
                <FileBox className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                <h4 className="text-base font-medium text-slate-700 dark:text-slate-300">
                  Ready to Convert
                </h4>
                <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
                  Upload a document, spreadsheet, presentation, image, audio, video, code file, or archive.
                  The converted output will preview here immediately with single-click download.
                </p>
              </div>
            )}

            {/* Converting state */}
            {isConverting && (
              <div className="my-auto text-center py-16">
                <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                <h4 className="text-base font-semibold text-slate-800 dark:text-slate-200">
                  Extracting and Normalizing Content...
                </h4>
                <p className="text-xs text-slate-500 mt-2">
                  Running format detection • Parsing AST / Media • Converting to {targetFormat.toUpperCase()}
                </p>
              </div>
            )}

            {/* Results presentation */}
            {conversionResult && !isConverting && (
              <div className="flex-1 flex flex-col space-y-4">
                {/* Status Bar */}
                <div className="flex flex-wrap items-center justify-between p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span className="font-semibold text-slate-900 dark:text-slate-100">
                      {conversionResult.output_filename}
                    </span>
                    <Badge variant="outline" className="uppercase text-[10px]">
                      {conversionResult.target_format}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-slate-500">
                    <span>Duration: {conversionResult.duration_seconds}s</span>
                    <span>Size: {(conversionResult.output_size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 text-xs">
                  <button
                    onClick={() => setPreviewTab("formatted")}
                    className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                      previewTab === "formatted"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Preview
                  </button>
                  <button
                    onClick={() => setPreviewTab("raw")}
                    className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                      previewTab === "raw"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Raw Content
                  </button>
                  {conversionResult.target_format === "zip" && (
                    <button
                      onClick={() => setPreviewTab("files")}
                      className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                        previewTab === "files"
                          ? "border-blue-600 text-blue-600"
                          : "border-transparent text-slate-500 hover:text-slate-800"
                      }`}
                    >
                      Bundle Files ({bundleFiles.length})
                    </button>
                  )}
                  <button
                    onClick={() => setPreviewTab("meta")}
                    className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                      previewTab === "meta"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Warnings & Info
                  </button>
                </div>

                {/* Tab Contents */}
                <div className="flex-1 overflow-auto rounded-lg bg-slate-50/50 dark:bg-slate-950/50 p-4 border border-slate-200 dark:border-slate-800 text-xs font-mono">
                  {previewTab === "formatted" && (
                    <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 font-sans whitespace-pre-wrap">
                      {conversionResult.preview_content || "No preview text generated."}
                    </div>
                  )}

                  {previewTab === "raw" && (
                    <pre className="text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
                      {conversionResult.preview_content}
                    </pre>
                  )}

                  {previewTab === "files" && (
                    <div className="space-y-2 font-sans">
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Files included in the complete Mode C extraction package:
                      </p>
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-300 dark:border-slate-700">
                            <th className="py-1.5">File Name</th>
                            <th className="py-1.5 text-right">Size</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bundleFiles.map((f, i) => (
                            <tr key={i} className="border-b border-slate-200 dark:border-slate-800/60">
                              <td className="py-1 font-mono text-blue-600 dark:text-blue-400">
                                {f.filename}
                              </td>
                              <td className="py-1 text-right text-slate-500">
                                {(f.size_bytes / 1024).toFixed(1)} KB
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {previewTab === "meta" && (
                    <div className="space-y-3 font-sans text-xs">
                      <div>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Source:</span>{" "}
                        {conversionResult.original_filename} ({conversionResult.source_format.toUpperCase()})
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Mode:</span>{" "}
                        {conversionResult.extraction_mode}
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Created At:</span>{" "}
                        {conversionResult.created_at}
                      </div>
                      {conversionResult.warnings.length > 0 && (
                        <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg text-amber-800 dark:text-amber-200">
                          <p className="font-semibold mb-1 flex items-center gap-1.5">
                            <AlertTriangle className="w-4 h-4 text-amber-600" /> Extraction Warnings:
                          </p>
                          <ul className="list-disc list-inside space-y-1">
                            {conversionResult.warnings.map((w, idx) => (
                              <li key={idx}>{w}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
