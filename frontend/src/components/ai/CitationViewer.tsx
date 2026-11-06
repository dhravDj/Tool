import React, { useState } from "react";
import { BookOpen, Check, Copy } from "lucide-react";
import { Citation } from "@/types/api";

interface CitationViewerProps {
  citations: Citation[];
  onSelectCitation?: (citation: Citation) => void;
}

export const CitationViewer: React.FC<CitationViewerProps> = ({
  citations,
  onSelectCitation,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!citations || citations.length === 0) {
    return null;
  }

  const handleCopy = (citation: Citation) => {
    const text = `[${citation.formatted_citation}]: "${citation.snippet}"`;
    navigator.clipboard.writeText(text);
    setCopiedId(citation.citation_id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
        <BookOpen className="w-3.5 h-3.5 text-blue-500" />
        <span>Verified Grounded Sources ({citations.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {citations.map((c) => {
          const isExpanded = expandedId === c.citation_id;
          return (
            <div
              key={c.citation_id}
              className={`p-2.5 rounded-lg border text-xs transition-all ${
                isExpanded
                  ? "bg-blue-50/50 dark:bg-blue-950/20 border-blue-300 dark:border-blue-700"
                  : "bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setExpandedId(isExpanded ? null : c.citation_id);
                    onSelectCitation?.(c);
                  }}
                  className="flex items-center gap-1.5 text-left font-medium text-slate-800 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-blue-100 dark:bg-blue-900/80 text-blue-700 dark:text-blue-300 font-bold text-[10px]">
                    {c.citation_id}
                  </span>
                  <span className="truncate max-w-[200px]" title={c.formatted_citation}>
                    {c.formatted_citation}
                  </span>
                </button>

                <div className="flex items-center gap-1">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase">
                    {c.source_type}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(c)}
                    className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded"
                    title="Copy citation"
                  >
                    {copiedId === c.citation_id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <p className="mt-1.5 text-slate-600 dark:text-slate-400 line-clamp-2 italic">
                &ldquo;{c.snippet}&rdquo;
              </p>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                  <div>
                    <span className="font-semibold">File:</span> {c.filename}
                  </div>
                  {c.page_number && (
                    <div>
                      <span className="font-semibold">Page:</span> {c.page_number}
                    </div>
                  )}
                  {c.sheet_name && (
                    <div>
                      <span className="font-semibold">Sheet:</span> {c.sheet_name}
                      {c.cell_range && ` (${c.cell_range})`}
                    </div>
                  )}
                  {c.slide_number && (
                    <div>
                      <span className="font-semibold">Slide:</span> {c.slide_number}
                    </div>
                  )}
                  {c.line_start && (
                    <div>
                      <span className="font-semibold">Lines:</span> {c.line_start}–{c.line_end || c.line_start}
                    </div>
                  )}
                  {c.timestamp_start !== undefined && c.timestamp_start !== null && (
                    <div>
                      <span className="font-semibold">Time:</span> {c.timestamp_start}s – {c.timestamp_end}s
                    </div>
                  )}
                  {c.archive_path && (
                    <div>
                      <span className="font-semibold">Archive Path:</span> {c.archive_path}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
