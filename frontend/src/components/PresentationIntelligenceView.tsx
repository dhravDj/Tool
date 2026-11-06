/** Presentation Intelligence View Component for DocuMind AI. */

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  BarChart2,
  ChevronLeft,
  ChevronRight,
  Download,
  EyeOff,
  FileText,
  Image as ImageIcon,
  Layers,
  Layout,
  Loader2,
  Mic,
  Monitor,
  Sparkles,
  Table as TableIcon,
} from "lucide-react";
import { api } from "@/services/api";
import {
  PresentationDocument,
  PresentationManifest,
  SlideChart,
  SlideData,
  SlideTable,
} from "@/types/api";

interface PresentationIntelligenceViewProps {
  fileId: string;
  filename: string;
  format?: string;
}

export const PresentationIntelligenceView: React.FC<PresentationIntelligenceViewProps> = ({
  fileId,
  filename,
  format = "pptx",
}) => {
  const [statusLoading, setStatusLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [canonicalDoc, setCanonicalDoc] = useState<PresentationDocument | null>(null);
  const [_manifest, setManifest] = useState<PresentationManifest | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Active slide and sub-view tab
  const [activeSlideIndex, setActiveSlideIndex] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<
    "slide_inspector" | "assets" | "speaker_notes" | "json"
  >("slide_inspector");

  const fetchPresentationData = async () => {
    setStatusLoading(true);
    setErrorMessage(null);
    try {
      const doc = await api.getPresentationDocumentResult(fileId);
      setCanonicalDoc(doc);
    } catch {
      // Analysis may not have been run yet
      setCanonicalDoc(null);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchPresentationData();
  }, [fileId]);

  const handleAnalyze = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzePresentationFile(fileId);
      setManifest(res);
      await fetchPresentationData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze presentation";
      setErrorMessage(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const currentSlide: SlideData | null =
    canonicalDoc && canonicalDoc.slides.length > activeSlideIndex
      ? canonicalDoc.slides[activeSlideIndex]
      : null;

  return (
    <div className="flex flex-col h-full bg-slate-900 text-slate-100 rounded-lg overflow-hidden border border-slate-800">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
            <Monitor className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-semibold tracking-tight text-white">{filename}</h2>
              <span className="px-2 py-0.5 text-xs font-medium uppercase tracking-wider rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {format}
              </span>
              {canonicalDoc?.metadata?.hidden_slide_count ? (
                <span className="flex items-center space-x-1 px-2 py-0.5 text-xs font-medium rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  <EyeOff className="w-3 h-3" />
                  <span>{canonicalDoc.metadata.hidden_slide_count} Hidden</span>
                </span>
              ) : null}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {canonicalDoc ? (
                <>
                  {canonicalDoc.slide_count} Slides • {canonicalDoc.presentation_dimensions.aspect_ratio} ({canonicalDoc.presentation_dimensions.width}″ × {canonicalDoc.presentation_dimensions.height}″) • {canonicalDoc.assets.length} Assets • {canonicalDoc.tables.length} Tables • {canonicalDoc.charts.length} Charts
                </>
              ) : (
                "Presentation Intelligence not yet computed."
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {canonicalDoc && (
            <div className="flex items-center space-x-2 border-r border-slate-800 pr-3">
              <a
                href={api.getPresentationDownloadUrl(fileId, "markdown")}
                download
                className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                title="Download formatted Markdown"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Markdown</span>
              </a>
              <a
                href={api.getPresentationDownloadUrl(fileId, "json")}
                download
                className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                title="Download canonical JSON"
              >
                <Download className="w-3.5 h-3.5" />
                <span>JSON</span>
              </a>
              <a
                href={api.getPresentationDownloadUrl(fileId, "text")}
                download
                className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                title="Download Plain Text"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Text</span>
              </a>
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={actionLoading}
            className="flex items-center space-x-2 px-4 py-2 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white shadow transition-colors"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>{canonicalDoc ? "Re-Analyze" : "Analyze Presentation"}</span>
          </button>
        </div>
      </div>

      {/* Warnings & Errors Banner */}
      {errorMessage && (
        <div className="flex items-center space-x-2 px-6 py-2.5 bg-rose-500/10 border-b border-rose-500/20 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {canonicalDoc && canonicalDoc.warnings.length > 0 && (
        <div className="flex items-center space-x-2 px-6 py-2 bg-amber-500/10 border-b border-amber-500/20 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>Warnings: {canonicalDoc.warnings.join(" | ")}</span>
        </div>
      )}

      {/* Main Body */}
      {statusLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-sm text-slate-400">Loading presentation intelligence data...</p>
        </div>
      ) : !canonicalDoc ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 mb-4">
            <Monitor className="w-8 h-8" />
          </div>
          <h3 className="text-base font-medium text-white mb-1">No Presentation Intelligence Data</h3>
          <p className="text-sm text-slate-400 max-w-md mb-6">
            Extract slide titles, paragraph bullet hierarchies, tables, native charts, diagrams, embedded images, and speaker notes.
          </p>
          <button
            onClick={handleAnalyze}
            disabled={actionLoading}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Run Presentation Intelligence</span>
          </button>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Slide Navigator */}
          <div className="w-72 bg-slate-950 border-r border-slate-800 flex flex-col">
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
              <span>Slides ({canonicalDoc.slides.length})</span>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setActiveSlideIndex(Math.max(0, activeSlideIndex - 1))}
                  disabled={activeSlideIndex === 0}
                  className="p-1 hover:bg-slate-800 rounded disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-slate-300">{activeSlideIndex + 1}/{canonicalDoc.slides.length}</span>
                <button
                  onClick={() => setActiveSlideIndex(Math.min(canonicalDoc.slides.length - 1, activeSlideIndex + 1))}
                  disabled={activeSlideIndex === canonicalDoc.slides.length - 1}
                  className="p-1 hover:bg-slate-800 rounded disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {canonicalDoc.slides.map((s, idx) => {
                const isSelected = idx === activeSlideIndex;
                return (
                  <button
                    key={s.slide_id}
                    onClick={() => setActiveSlideIndex(idx)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? "bg-indigo-600/10 border-indigo-500 text-white shadow-sm"
                        : "bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/60 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-semibold ${isSelected ? "text-indigo-400" : "text-slate-500"}`}>
                        Slide {s.slide_number}
                      </span>
                      {s.hidden && (
                        <span className="flex items-center space-x-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                          <EyeOff className="w-2.5 h-2.5" />
                          <span>Hidden</span>
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-medium line-clamp-1">
                      {s.title || "Untitled Slide"}
                    </p>
                    <div className="flex items-center space-x-2 mt-2 text-[10px] text-slate-500">
                      <span>{s.elements.length} elements</span>
                      {s.speaker_notes && (
                        <span className="flex items-center space-x-0.5 text-indigo-400">
                          <Mic className="w-2.5 h-2.5" />
                          <span>Notes</span>
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column: Content Inspector */}
          <div className="flex-1 flex flex-col bg-slate-900 overflow-hidden">
            {/* Tab navigation */}
            <div className="flex items-center justify-between px-6 border-b border-slate-800 bg-slate-950/40">
              <div className="flex space-x-6">
                <button
                  onClick={() => setActiveTab("slide_inspector")}
                  className={`flex items-center space-x-2 py-3 text-xs font-medium border-b-2 transition-colors ${
                    activeTab === "slide_inspector"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Layout className="w-4 h-4" />
                  <span>Slide Inspector</span>
                </button>
                <button
                  onClick={() => setActiveTab("assets")}
                  className={`flex items-center space-x-2 py-3 text-xs font-medium border-b-2 transition-colors ${
                    activeTab === "assets"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <ImageIcon className="w-4 h-4" />
                  <span>Assets ({canonicalDoc.assets.length})</span>
                </button>
                <button
                  onClick={() => setActiveTab("speaker_notes")}
                  className={`flex items-center space-x-2 py-3 text-xs font-medium border-b-2 transition-colors ${
                    activeTab === "speaker_notes"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Mic className="w-4 h-4" />
                  <span>Speaker Notes ({canonicalDoc.speaker_notes.length})</span>
                </button>
                <button
                  onClick={() => setActiveTab("json")}
                  className={`flex items-center space-x-2 py-3 text-xs font-medium border-b-2 transition-colors ${
                    activeTab === "json"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>Canonical JSON</span>
                </button>
              </div>
            </div>

            {/* Tab Contents */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === "slide_inspector" && currentSlide && (
                <div className="max-w-4xl mx-auto space-y-6">
                  {/* Slide Title Box */}
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                      <span>SLIDE {currentSlide.slide_number} OF {canonicalDoc.slide_count}</span>
                      {currentSlide.hidden && (
                        <span className="text-amber-400 font-medium">HIDDEN SLIDE</span>
                      )}
                    </div>
                    <h3 className="text-xl font-bold text-white tracking-tight">
                      {currentSlide.title || "Untitled Slide"}
                    </h3>
                  </div>

                  {/* Slide Elements Stream */}
                  <div className="space-y-4">
                    {currentSlide.elements.map((elem) => {
                      if (elem.element_type === "title") {
                        return null; // Shown above
                      }

                      if (elem.element_type === "text") {
                        return (
                          <div
                            key={elem.element_id}
                            className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-lg space-y-2"
                          >
                            {elem.paragraphs && elem.paragraphs.length > 0 ? (
                              elem.paragraphs.map((p, pIdx) => (
                                <div
                                  key={pIdx}
                                  style={{ paddingLeft: `${p.level * 20}px` }}
                                  className="flex items-start space-x-2 text-sm text-slate-200"
                                >
                                  {p.bullet || p.level > 0 ? (
                                    <span className="text-indigo-400 mt-1">•</span>
                                  ) : null}
                                  <div className="flex-1">
                                    {p.runs && p.runs.length > 0 ? (
                                      p.runs.map((r, rIdx) => (
                                        <span
                                          key={rIdx}
                                          className={`inline ${r.bold ? "font-bold text-white" : ""} ${
                                            r.italic ? "italic" : ""
                                          } ${r.underline ? "underline" : ""}`}
                                        >
                                          {r.text}
                                        </span>
                                      ))
                                    ) : (
                                      <span>{p.text}</span>
                                    )}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-slate-300">{elem.text}</p>
                            )}
                          </div>
                        );
                      }

                      if (elem.element_type === "table" && elem.raw_data) {
                        const tbl = elem.raw_data as unknown as SlideTable;
                        return (
                          <div
                            key={elem.element_id}
                            className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3"
                          >
                            <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                              <TableIcon className="w-4 h-4" />
                              <span>Table ({tbl.rows_count} rows × {tbl.columns_count} cols)</span>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs text-left text-slate-300 border-collapse">
                                <tbody>
                                  {tbl.rows?.map((row, rIdx) => (
                                    <tr
                                      key={rIdx}
                                      className={`border-b border-slate-800 ${
                                        rIdx === 0 && tbl.has_header ? "bg-slate-800/50 font-semibold text-white" : ""
                                      }`}
                                    >
                                      {row.map((cell, cIdx) => (
                                        <td key={cIdx} className="px-3 py-2 border-r border-slate-800/50 last:border-r-0">
                                          {cell.text}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        );
                      }

                      if (elem.element_type === "chart" && elem.raw_data) {
                        const ch = elem.raw_data as unknown as SlideChart;
                        return (
                          <div
                            key={elem.element_id}
                            className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                                <BarChart2 className="w-4 h-4" />
                                <span>Chart: {ch.chart_type}</span>
                              </div>
                              {ch.title && <span className="text-xs text-white font-medium">{ch.title}</span>}
                            </div>

                            {ch.categories && ch.series && ch.categories.length > 0 && (
                              <div className="overflow-x-auto text-xs">
                                <table className="w-full text-slate-300 border-collapse">
                                  <thead>
                                    <tr className="border-b border-slate-800 bg-slate-800/40 text-white font-semibold">
                                      <th className="px-3 py-2 text-left">Category</th>
                                      {ch.series.map((s, sIdx) => (
                                        <th key={sIdx} className="px-3 py-2 text-right">{s.name}</th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {ch.categories.map((cat, cIdx) => (
                                      <tr key={cIdx} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                                        <td className="px-3 py-1.5 font-medium text-slate-300">{cat}</td>
                                        {ch.series.map((s, sIdx) => (
                                          <td key={sIdx} className="px-3 py-1.5 text-right font-mono text-slate-400">
                                            {s.values[cIdx] ?? "-"}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        );
                      }

                      if (elem.element_type === "image") {
                        return (
                          <div
                            key={elem.element_id}
                            className="p-4 bg-slate-950 border border-slate-800 rounded-lg flex items-center space-x-3 text-xs text-slate-300"
                          >
                            <div className="p-2 bg-slate-800 rounded text-indigo-400">
                              <ImageIcon className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="font-medium text-white">{elem.text}</p>
                              <p className="text-[10px] text-slate-500">Ref: {elem.asset_reference || "N/A"}</p>
                            </div>
                          </div>
                        );
                      }

                      if (elem.element_type === "group") {
                        return (
                          <div
                            key={elem.element_id}
                            className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg space-y-2"
                          >
                            <div className="flex items-center space-x-2 text-xs font-semibold text-purple-400 uppercase tracking-wider">
                              <Layers className="w-4 h-4" />
                              <span>{elem.text}</span>
                            </div>
                            {elem.relationships && elem.relationships.length > 0 && (
                              <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                                {elem.relationships.map((rel: any, idx: number) => (
                                  <div key={idx} className="p-2 bg-slate-900 border border-slate-800 rounded">
                                    <span className="font-medium text-slate-200">{rel.name || "Item"}: </span>
                                    <span>{rel.text || "No text"}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      }

                      return (
                        <div
                          key={elem.element_id}
                          className="p-3 bg-slate-950 border border-slate-800/80 rounded-lg text-xs text-slate-400"
                        >
                          <span className="font-semibold text-slate-300">{elem.element_type.toUpperCase()}: </span>
                          <span>{elem.text}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Speaker Notes Callout */}
                  {currentSlide.speaker_notes && currentSlide.speaker_notes.trim() && (
                    <div className="p-4 bg-indigo-950/30 border border-indigo-500/30 rounded-lg space-y-2">
                      <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                        <Mic className="w-4 h-4" />
                        <span>Speaker Notes</span>
                      </div>
                      <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                        {currentSlide.speaker_notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "assets" && (
                <div className="max-w-4xl mx-auto space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-white">Extracted Embedded Assets</h3>
                    <span className="text-xs text-slate-400">{canonicalDoc.assets.length} items</span>
                  </div>

                  {canonicalDoc.assets.length === 0 ? (
                    <p className="text-xs text-slate-500 py-8 text-center">No embedded images or media in this presentation.</p>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {canonicalDoc.assets.map((asset) => (
                        <div
                          key={asset.asset_id}
                          className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-slate-800 text-slate-300 rounded">
                              {asset.format}
                            </span>
                            <span className="text-[10px] text-slate-500">Slide {asset.slide_number}</span>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-white truncate">
                              {asset.original_filename || asset.asset_id}
                            </p>
                            <p className="text-[10px] text-slate-400 mt-0.5">
                              {(asset.size_bytes / 1024).toFixed(1)} KB • SHA256: {asset.sha256.slice(0, 12)}...
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === "speaker_notes" && (
                <div className="max-w-4xl mx-auto space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-white">Speaker Notes by Slide</h3>
                    <span className="text-xs text-slate-400">{canonicalDoc.speaker_notes.length} slides with notes</span>
                  </div>

                  {canonicalDoc.speaker_notes.length === 0 ? (
                    <p className="text-xs text-slate-500 py-8 text-center">This presentation does not contain any speaker notes.</p>
                  ) : (
                    canonicalDoc.speaker_notes.map((n) => (
                      <div
                        key={n.slide_id}
                        className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs text-indigo-400 font-semibold">
                          <span>Slide {n.slide_number}</span>
                          <span className="text-[10px] text-slate-500 font-normal">{n.word_count} words</span>
                        </div>
                        <p className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                          {n.text}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "json" && (
                <div className="max-w-4xl mx-auto">
                  <pre className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-[600px]">
                    {JSON.stringify(canonicalDoc, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
