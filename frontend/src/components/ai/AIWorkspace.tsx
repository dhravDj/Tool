import React, { useState } from "react";
import {
  Columns,
  FileText,
  GitCompare,
  MessageSquare,
  Search,
  Settings,
} from "lucide-react";
import { FileChatView } from "./FileChatView";
import { KnowledgeSearchView } from "./KnowledgeSearchView";
import { AISettingsView } from "./AISettingsView";
import { CitationViewer } from "./CitationViewer";
import { api } from "@/services/api";
import { ComparisonResponse, SummaryResponse } from "@/types/api";

interface AIWorkspaceProps {
  selectedFileId?: string;
  selectedFilename?: string;
}

export const AIWorkspace: React.FC<AIWorkspaceProps> = ({
  selectedFileId,
  selectedFilename,
}) => {
  const [activeTab, setActiveTab] = useState<"chat" | "search" | "summary" | "settings">("chat");

  // Summary State
  const [summaryType, setSummaryType] = useState<string>("executive");
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  // Compare State
  const [compareIdsInput, setCompareIdsInput] = useState<string>("");
  const [compareData, setCompareData] = useState<ComparisonResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const handleSummarize = async () => {
    if (!selectedFileId) return;
    setIsSummarizing(true);
    try {
      const res = await api.summarizeFile({
        file_id: selectedFileId,
        summary_type: summaryType,
      });
      setSummaryData(res);
    } catch (e) {
      console.error("Summarization error:", e);
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleCompare = async () => {
    const ids = compareIdsInput
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (ids.length < 2) return;
    setIsComparing(true);
    try {
      const res = await api.compareFiles({ file_ids: ids });
      setCompareData(res);
    } catch (e) {
      console.error("Comparison error:", e);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Workspace Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2 gap-2">
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setActiveTab("chat")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "chat"
                ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            File Chat &amp; Q&amp;A
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("search")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "search"
                ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            Hybrid Knowledge Search
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("summary")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "summary"
                ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            Summaries &amp; Compare
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("settings")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "settings"
                ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            AI Settings
          </button>
        </div>

        {selectedFilename && (
          <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span className="font-medium text-slate-700 dark:text-slate-300 truncate max-w-[240px]">
              {selectedFilename}
            </span>
          </div>
        )}
      </div>

      {/* Tab Panels */}
      {activeTab === "chat" && (
        <FileChatView
          selectedFileId={selectedFileId}
          selectedFilename={selectedFilename}
        />
      )}

      {activeTab === "search" && <KnowledgeSearchView />}

      {activeTab === "summary" && (
        <div className="space-y-6">
          {/* Single File Summarization Card */}
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-500" />
                Single-File Multi-Type Summarization
              </h4>
            </div>

            {selectedFileId ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <select
                    value={summaryType}
                    onChange={(e) => setSummaryType(e.target.value)}
                    className="text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-hidden"
                  >
                    <option value="short">Short (2-3 sentences)</option>
                    <option value="detailed">Detailed Narrative</option>
                    <option value="executive">Executive Summary</option>
                    <option value="bullet">Bullet Takeaways</option>
                    <option value="technical">Technical Dossier</option>
                    <option value="key_findings">Key Findings List</option>
                  </select>

                  <button
                    type="button"
                    onClick={handleSummarize}
                    disabled={isSummarizing}
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all shadow-xs"
                  >
                    {isSummarizing ? "Generating..." : "Generate Summary"}
                  </button>
                </div>

                {summaryData && (
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
                    <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Summary for {summaryData.filename} ({summaryData.summary_type.toUpperCase()})
                    </div>
                    <div className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {summaryData.summary_text}
                    </div>

                    {summaryData.key_findings && summaryData.key_findings.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                        <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 mb-1.5">
                          Verified Key Findings
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-xs text-slate-600 dark:text-slate-400">
                          {summaryData.key_findings.map((kf, i) => (
                            <li key={i}>{kf}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {summaryData.citations && (
                      <CitationViewer citations={summaryData.citations} />
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Please select a file from the file library to generate an AI summary.
              </p>
            )}
          </div>

          {/* Multi-File Comparison Card */}
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
            <div className="flex items-center gap-2 mb-3">
              <Columns className="w-4 h-4 text-emerald-500" />
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Cross-File Comparison &amp; Contradiction Detection
              </h4>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
              Enter 2 or more file UUIDs (comma-separated) to perform deep comparative analysis, alignment matrix construction, and two-sided contradiction detection.
            </p>

            <div className="flex items-center gap-2 mb-4">
              <input
                type="text"
                value={compareIdsInput}
                onChange={(e) => setCompareIdsInput(e.target.value)}
                placeholder="UUID1, UUID2, ..."
                className="flex-1 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-mono text-slate-800 dark:text-slate-200 focus:outline-hidden"
              />
              <button
                type="button"
                onClick={handleCompare}
                disabled={isComparing}
                className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-xs"
              >
                {isComparing ? "Comparing..." : "Run Comparison"}
              </button>
            </div>

            {compareData && (
              <div className="space-y-4">
                {/* Matrix */}
                <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                  <table className="w-full text-xs text-left text-slate-700 dark:text-slate-300">
                    <thead className="bg-slate-100 dark:bg-slate-800 font-semibold border-b border-slate-200 dark:border-slate-700">
                      <tr>
                        <th className="p-2.5">Aspect</th>
                        {compareData.filenames.map((fn, i) => (
                          <th key={i} className="p-2.5 truncate max-w-[200px]">{fn}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {compareData.comparison_matrix.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                          <td className="p-2.5 font-medium">{row.aspect}</td>
                          {compareData.filenames.map((fn, j) => (
                            <td key={j} className="p-2.5 font-mono">{row[fn] || "-"}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Contradictions */}
                {compareData.contradictions && compareData.contradictions.length > 0 && (
                  <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 space-y-2">
                    <h5 className="text-xs font-bold text-amber-900 dark:text-amber-200 uppercase tracking-wider">
                      Detected Discrepancies &amp; Contradictions ({compareData.contradictions.length})
                    </h5>
                    {compareData.contradictions.map((ct, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-amber-100 dark:border-amber-900/40 text-xs space-y-1">
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{ct.topic}</div>
                        <div className="text-slate-600 dark:text-slate-400">• {ct.file_a_claim}</div>
                        <div className="text-slate-600 dark:text-slate-400">• {ct.file_b_claim}</div>
                        <div className="text-[11px] text-amber-700 dark:text-amber-300 italic">Resolution: {ct.resolution}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Synthesis */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 mb-1.5">
                    Consolidated Multi-File Synthesis
                  </div>
                  <div className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                    {compareData.consolidated_summary}
                  </div>
                </div>

                {compareData.citations && (
                  <CitationViewer citations={compareData.citations} />
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "settings" && <AISettingsView />}
    </div>
  );
};
