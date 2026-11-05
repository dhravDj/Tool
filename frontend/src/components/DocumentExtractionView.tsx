import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowDownToLine,
  CheckCircle2,
  Clock,
  Code,
  Copy,
  FileJson,
  FileText,
  Layers,
  ListOrdered,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { api } from "@/services/api";
import { BlockType, CanonicalDocument, ExtractionManifest, ExtractionStatusResponse } from "@/types/api";

interface DocumentExtractionViewProps {
  fileId: string;
  filename: string;
  formatId?: string;
  onClose?: () => void;
}

export const DocumentExtractionView: React.FC<DocumentExtractionViewProps> = ({
  fileId,
  filename,
  formatId,
}) => {
  const [activeTab, setActiveTab] = useState<"markdown" | "blocks" | "json" | "manifest">("markdown");
  const [selectedPage, setSelectedPage] = useState<number>(1);
  const [copied, setCopied] = useState(false);
  const [password, setPassword] = useState("");
  const [extractImages, setExtractImages] = useState(false);

  // 1. Fetch extraction status and outputs
  const {
    data: extractionStatus,
    refetch: refetchStatus,
  } = useQuery<ExtractionStatusResponse>({
    queryKey: ["extraction-status", fileId],
    queryFn: () => api.getExtractionStatus(fileId),
    retry: 1,
  });

  // 2. Fetch canonical document if extraction completed
  const { data: canonicalDoc, refetch: refetchCanonical } = useQuery<CanonicalDocument>({
    queryKey: ["canonical-doc", fileId],
    queryFn: () => api.getCanonicalDocument(fileId),
    enabled: !!extractionStatus && extractionStatus.status !== "failed",
    retry: 1,
  });

  // 3. Fetch extracted markdown text
  const { data: markdownText, refetch: refetchMarkdown } = useQuery<string>({
    queryKey: ["extracted-markdown", fileId],
    queryFn: () => api.getExtractedMarkdown(fileId),
    enabled: !!extractionStatus && extractionStatus.status !== "failed",
    retry: 1,
  });

  // 4. Fetch extraction manifest
  const { data: manifest, refetch: refetchManifest } = useQuery<ExtractionManifest>({
    queryKey: ["extraction-manifest", fileId],
    queryFn: () => api.getExtractionManifest(fileId),
    enabled: !!extractionStatus && extractionStatus.status !== "failed",
    retry: 1,
  });

  // Extract Mutation
  const extractMutation = useMutation({
    mutationFn: () =>
      api.extractDocument(fileId, {
        password: password.trim() || undefined,
        extract_images: extractImages,
      }),
    onSuccess: () => {
      refetchStatus();
      refetchCanonical();
      refetchMarkdown();
      refetchManifest();
    },
  });

  const handleCopyMarkdown = () => {
    if (markdownText) {
      navigator.clipboard.writeText(markdownText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadFile = (content: string, ext: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}_extracted.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getBlockTypeBadgeColor = (type: BlockType) => {
    switch (type) {
      case "heading":
        return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800";
      case "table":
        return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800";
      case "code":
        return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800";
      case "list_item":
        return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
      case "header":
      case "footer":
        return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700";
      case "image_reference":
        return "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 border-rose-200 dark:border-rose-800";
      default:
        return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700";
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-card border border-border">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <h2 className="text-base font-semibold text-foreground truncate max-w-md">
              {filename}
            </h2>
            {formatId && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground uppercase font-semibold">
                {formatId}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Phase 3 Document Extraction: structure, tables, metadata, and reading order preservation.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {extractionStatus ? (
            <>
              {markdownText && (
                <button
                  onClick={() => handleDownloadFile(markdownText, "md", "text/markdown")}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-background hover:bg-muted text-foreground transition"
                  title="Download Markdown"
                >
                  <ArrowDownToLine className="h-3.5 w-3.5" />
                  Markdown
                </button>
              )}
              {canonicalDoc && (
                <button
                  onClick={() =>
                    handleDownloadFile(JSON.stringify(canonicalDoc, null, 2), "json", "application/json")
                  }
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-background hover:bg-muted text-foreground transition"
                  title="Download Canonical JSON"
                >
                  <FileJson className="h-3.5 w-3.5" />
                  JSON
                </button>
              )}
              <button
                onClick={() => extractMutation.mutate()}
                disabled={extractMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition disabled:opacity-50"
              >
                {extractMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="h-3.5 w-3.5" />
                )}
                Re-Extract
              </button>
            </>
          ) : (
            <button
              onClick={() => extractMutation.mutate()}
              disabled={extractMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition shadow-sm disabled:opacity-50"
            >
              {extractMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Extract Content
            </button>
          )}
        </div>
      </div>

      {/* Optional Password or Extraction Options Bar if not yet extracted */}
      {!extractionStatus && (
        <div className="p-3.5 rounded-xl bg-muted/40 border border-border/80 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <span className="text-muted-foreground whitespace-nowrap">PDF Password (if protected):</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Leave blank if unencrypted"
              className="px-2.5 py-1 rounded bg-background border border-border text-foreground text-xs w-full max-w-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <label className="flex items-center gap-2 text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={extractImages}
              onChange={(e) => setExtractImages(e.target.checked)}
              className="rounded border-border text-primary focus:ring-0"
            />
            Extract embedded images to assets
          </label>
        </div>
      )}

      {/* Mutation Error / Warning */}
      {extractMutation.isError && (
        <div className="p-3.5 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>Extraction Failed: {(extractMutation.error as Error).message}</span>
        </div>
      )}

      {/* Extraction Execution Summary Banner */}
      {extractionStatus && (
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">Status</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-xs font-semibold capitalize text-foreground">
                {extractionStatus.status.replace(/_/g, " ")}
              </span>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">Engine</span>
            <span className="text-xs font-semibold font-mono text-foreground mt-0.5 block truncate">
              {extractionStatus.engine}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">Pages</span>
            <span className="text-xs font-semibold text-foreground mt-0.5 block">
              {extractionStatus.page_count} page{extractionStatus.page_count === 1 ? "" : "s"}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">Extracted Blocks</span>
            <span className="text-xs font-semibold text-foreground mt-0.5 block">
              {extractionStatus.block_count} blocks
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">OCR Routed</span>
            <span className="text-xs font-semibold text-foreground mt-0.5 block">
              {extractionStatus.ocr_applied_pages} / {extractionStatus.scanned_pages} scanned
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-card border border-border">
            <span className="text-[10px] text-muted-foreground block font-medium">Duration</span>
            <span className="text-xs font-semibold text-foreground mt-0.5 block flex items-center gap-1">
              <Clock className="h-3 w-3 text-muted-foreground" />
              {manifest?.execution_time_seconds ? `${manifest.execution_time_seconds}s` : "< 0.1s"}
            </span>
          </div>
        </div>
      )}

      {/* Warnings & Errors */}
      {extractionStatus?.warnings && extractionStatus.warnings.length > 0 && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-200 text-xs">
          <div className="flex items-center gap-1.5 font-semibold mb-1">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
            Extraction Warnings ({extractionStatus.warnings.length})
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-[11px] opacity-90">
            {extractionStatus.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tabs */}
      {extractionStatus && (
        <div className="space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-1">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab("markdown")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === "markdown"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                Markdown Preview
              </button>
              <button
                onClick={() => setActiveTab("blocks")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === "blocks"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                Structural Blocks
              </button>
              <button
                onClick={() => setActiveTab("json")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === "json"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <Code className="h-3.5 w-3.5" />
                Canonical JSON
              </button>
              <button
                onClick={() => setActiveTab("manifest")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                  activeTab === "manifest"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <ListOrdered className="h-3.5 w-3.5" />
                Manifest
              </button>
            </div>

            {activeTab === "markdown" && markdownText && (
              <button
                onClick={handleCopyMarkdown}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground rounded border border-border/80 transition"
              >
                {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>

          {/* TAB 1: Markdown Preview */}
          {activeTab === "markdown" && (
            <div className="p-4 rounded-xl bg-card border border-border min-h-[300px] max-h-[550px] overflow-y-auto">
              {markdownText ? (
                <div className="prose dark:prose-invert max-w-none text-xs leading-relaxed font-sans whitespace-pre-wrap">
                  {markdownText}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground text-xs">
                  No extracted markdown content available.
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Structural Blocks Inspector */}
          {activeTab === "blocks" && canonicalDoc && (
            <div className="space-y-3">
              {canonicalDoc.pages.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                  <span className="text-muted-foreground text-[11px] font-medium mr-1">Pages:</span>
                  {canonicalDoc.pages.map((p) => (
                    <button
                      key={p.page_number}
                      onClick={() => setSelectedPage(p.page_number)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                        selectedPage === p.page_number
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Page {p.page_number}
                      {p.is_scanned && " (Scanned)"}
                    </button>
                  ))}
                </div>
              )}

              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                {canonicalDoc.pages
                  .find((p) => p.page_number === selectedPage)
                  ?.blocks.map((block, idx) => (
                    <div
                      key={block.block_id || idx}
                      className="p-3 rounded-lg bg-card border border-border/80 space-y-1.5 text-xs hover:border-primary/40 transition"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap text-[11px]">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase tracking-wider ${getBlockTypeBadgeColor(
                              block.block_type
                            )}`}
                          >
                            {block.block_type}
                          </span>
                          <span className="text-muted-foreground font-mono text-[10px]">
                            Order: #{block.reading_order}
                          </span>
                          <span className="text-muted-foreground text-[10px]">
                            Source: {block.provenance}
                          </span>
                        </div>
                        {block.bounding_box && (
                          <span className="text-[10px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            bbox: [{block.bounding_box.map((n) => Math.round(n)).join(", ")}]
                          </span>
                        )}
                      </div>

                      {/* Content rendering */}
                      {block.block_type === "table" && block.metadata?.table_grid ? (
                        <div className="overflow-x-auto my-2 rounded border border-border/60">
                          <table className="w-full text-left border-collapse text-[11px]">
                            <tbody>
                              {(block.metadata.table_grid as string[][]).map((row, rIdx) => (
                                <tr
                                  key={rIdx}
                                  className={rIdx === 0 ? "bg-muted/60 font-semibold" : "border-t border-border/40"}
                                >
                                  {row.map((cell, cIdx) => (
                                    <td key={cIdx} className="p-1.5 border-r border-border/40 last:border-r-0">
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-foreground whitespace-pre-wrap leading-relaxed font-sans">
                          {block.text}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* TAB 3: Canonical Document JSON */}
          {activeTab === "json" && canonicalDoc && (
            <div className="p-3 rounded-xl bg-muted/30 border border-border max-h-[500px] overflow-auto">
              <pre className="text-[11px] font-mono text-foreground whitespace-pre">
                {JSON.stringify(canonicalDoc, null, 2)}
              </pre>
            </div>
          )}

          {/* TAB 4: Operational Manifest */}
          {activeTab === "manifest" && manifest && (
            <div className="p-4 rounded-xl bg-card border border-border max-h-[500px] overflow-auto space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-muted/40">
                <div>
                  <span className="text-muted-foreground text-[10px] block">Document ID:</span>
                  <span className="font-mono text-[11px] text-foreground">{manifest.document_id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-[10px] block">Processed At:</span>
                  <span className="text-[11px] text-foreground">{manifest.processing_timestamp}</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-[10px] block">Total Duration:</span>
                  <span className="text-[11px] text-foreground">{manifest.execution_time_seconds}s</span>
                </div>
                <div>
                  <span className="text-muted-foreground text-[10px] block">Confidence:</span>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">
                    {Math.round(manifest.overall_confidence * 100)}%
                  </span>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-foreground mb-1.5">Output Artifact Map:</h4>
                <div className="space-y-1 font-mono text-[11px]">
                  {Object.entries(manifest.output_files).map(([key, val]) => (
                    <div key={key} className="p-2 rounded bg-muted/30 border border-border/50 flex justify-between">
                      <span className="font-medium text-foreground">{key}:</span>
                      <span className="text-muted-foreground">{val}</span>
                    </div>
                  ))}
                </div>
              </div>

              {manifest.assets && manifest.assets.length > 0 && (
                <div>
                  <h4 className="font-semibold text-foreground mb-1.5">Extracted Assets:</h4>
                  <div className="space-y-1 text-[11px]">
                    {manifest.assets.map((asset, idx) => (
                      <div key={idx} className="p-2 rounded bg-muted/30 border border-border/50 flex justify-between">
                        <span>{String(asset.name || idx)}</span>
                        <span className="text-muted-foreground font-mono">{String(asset.size)} bytes</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
