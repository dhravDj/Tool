/** Image & Visual Intelligence Inspector Component for DocuMind AI. */

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  BarChart2,
  Bot,
  ChevronRight,
  Download,
  Eye,
  FileImage,
  GitBranch,
  Layers,
  Loader2,
  Lock,
  MessageSquare,
  Sparkles,
  Type,
} from "lucide-react";
import { api } from "@/services/api";
import {
  ImageAnalysisStatusResponse,
  ImageAskResponse,
  ImageDocument,
  ImageRegion,
} from "@/types/api";

interface ImageIntelligenceViewProps {
  fileId: string;
  filename: string;
  format?: string;
}

export const ImageIntelligenceView: React.FC<ImageIntelligenceViewProps> = ({
  fileId,
  filename,
  format = "image",
}) => {
  const [statusLoading, setStatusLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [_statusData, setStatusData] = useState<ImageAnalysisStatusResponse | null>(null);
  const [canonicalDoc, setCanonicalDoc] = useState<ImageDocument | null>(null);
  const [activeTab, setActiveTab] = useState<"visual" | "ocr" | "insights" | "vqa" | "json">("visual");
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [selectedRegion, setSelectedRegion] = useState<ImageRegion | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // VQA State
  const [vqaQuestion, setVqaQuestion] = useState<string>("");
  const [vqaLoading, setVqaLoading] = useState<boolean>(false);
  const [vqaHistory, setVqaHistory] = useState<ImageAskResponse[]>([]);

  const fetchAnalysisData = async () => {
    setStatusLoading(true);
    setErrorMessage(null);
    try {
      const statusRes = await api.getImageAnalysisStatus(fileId);
      setStatusData(statusRes);
      if (statusRes.status.includes("completed")) {
        const docRes = await api.getCanonicalImageDocument(fileId);
        setCanonicalDoc(docRes);
      }
    } catch {
      setStatusData(null);
      setCanonicalDoc(null);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysisData();
  }, [fileId]);

  const handleRunAnalysis = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.analyzeImage(fileId);
      await fetchAnalysisData();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to analyze image.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vqaQuestion.trim()) return;

    setVqaLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.askImageQuestion(fileId, vqaQuestion);
      setVqaHistory((prev) => [res, ...prev]);
      setVqaQuestion("");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Visual QA query failed.");
    } finally {
      setVqaLoading(false);
    }
  };

  const downloadFile = (content: string, name: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredRegions = canonicalDoc?.regions.filter((r) => {
    if (regionFilter === "all") return true;
    return r.region_type === regionFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-card border border-border rounded-xl shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-primary/10 text-primary rounded-lg">
            <FileImage className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-foreground">{filename}</h2>
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-muted text-muted-foreground uppercase">
                {format}
              </span>
              {canonicalDoc?.metadata.gps_redacted && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/10 text-emerald-600 flex items-center gap-1">
                  <Lock className="w-3 h-3" /> GPS Sanitized
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              {canonicalDoc ? (
                <>
                  {canonicalDoc.metadata.width} × {canonicalDoc.metadata.height} px • {canonicalDoc.metadata.color_mode} • {canonicalDoc.regions.length} detected visual regions
                </>
              ) : (
                "Image & Visual Intelligence analysis pending"
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {canonicalDoc && (
            <>
              <button
                onClick={() =>
                  downloadFile(
                    JSON.stringify(canonicalDoc, null, 2),
                    `${filename}_visual_intelligence.json`,
                    "application/json"
                  )
                }
                className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-border bg-background hover:bg-muted text-foreground transition-colors"
                title="Download Canonical JSON"
              >
                <Download className="w-3.5 h-3.5" />
                <span>JSON</span>
              </button>
            </>
          )}

          <button
            onClick={handleRunAnalysis}
            disabled={actionLoading}
            className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-semibold rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-colors disabled:opacity-50"
          >
            {actionLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing Image...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>{canonicalDoc ? "Re-Analyze" : "Analyze Visual Intelligence"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {statusLoading ? (
        <div className="flex items-center justify-center p-16 bg-card border border-border rounded-xl">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-sm text-muted-foreground">Checking visual intelligence records...</span>
        </div>
      ) : !canonicalDoc ? (
        <div className="text-center p-12 bg-card border border-border border-dashed rounded-xl">
          <Bot className="w-12 h-12 mx-auto text-muted-foreground/60 mb-3" />
          <h3 className="text-base font-semibold text-foreground">No Visual Intelligence Extracted Yet</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mt-1 mb-6">
            Execute the Image & Visual Intelligence Engine to extract OCR text, scene captions, objects, flowcharts, charts, and enable Visual QA.
          </p>
          <button
            onClick={handleRunAnalysis}
            disabled={actionLoading}
            className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>Run Visual Analysis</span>
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* AI Scene Summary Card */}
          <div className="p-5 bg-gradient-to-r from-primary/5 via-card to-background border border-border rounded-xl">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 text-xs font-bold rounded bg-primary/20 text-primary">
                    AI Visual Summary
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">
                    Scene: {canonicalDoc.analysis.scene_type}
                  </span>
                </div>
                <p className="text-base font-medium text-foreground leading-relaxed pt-1">
                  {canonicalDoc.analysis.caption}
                </p>
              </div>

              {canonicalDoc.analysis.dominant_colors.length > 0 && (
                <div className="flex items-center space-x-1.5 p-2 bg-card border border-border rounded-lg flex-shrink-0">
                  <span className="text-xs text-muted-foreground mr-1">Palette:</span>
                  {canonicalDoc.analysis.dominant_colors.map((color, idx) => (
                    <div
                      key={idx}
                      className="w-5 h-5 rounded-full border border-black/10 shadow-xs"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-border space-x-2">
            {[
              { id: "visual", label: "Visual Inspector", icon: Eye, count: canonicalDoc.regions.length },
              { id: "ocr", label: "OCR Text Layer", icon: Type, count: canonicalDoc.analysis.ocr_word_count },
              {
                id: "insights",
                label: "Diagrams & Charts",
                icon: BarChart2,
                badge: canonicalDoc.analysis.diagram.is_diagram || canonicalDoc.analysis.chart.is_chart,
              },
              { id: "vqa", label: "Visual Q&A (VQA)", icon: MessageSquare },
              { id: "json", label: "Canonical JSON", icon: Layers },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && (
                    <span className="ml-1 px-1.5 py-0.2 text-xs rounded-full bg-muted text-muted-foreground">
                      {tab.count}
                    </span>
                  )}
                  {tab.badge && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>

          {/* TAB 1: Visual Inspector */}
          {activeTab === "visual" && (
            <div className="space-y-4">
              {/* Region Filter Bar */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium text-muted-foreground">Filter Regions:</span>
                  {["all", "text", "object", "diagram", "chart"].map((f) => (
                    <button
                      key={f}
                      onClick={() => setRegionFilter(f)}
                      className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors capitalize ${
                        regionFilter === f
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
                <span className="text-xs text-muted-foreground">
                  Showing {filteredRegions.length} of {canonicalDoc.regions.length} regions
                </span>
              </div>

              {/* Bounding Box Visualizer & Details Split */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Visual Viewport with Bounding Boxes */}
                <div className="lg:col-span-2 p-6 bg-card border border-border rounded-xl relative min-h-[420px] flex items-center justify-center overflow-hidden">
                  <div
                    className="relative w-full max-w-[560px] aspect-[4/3] bg-muted/40 border border-border/80 rounded-lg overflow-hidden shadow-inner flex items-center justify-center"
                    style={{ aspectRatio: `${canonicalDoc.metadata.aspect_ratio || 1.33}` }}
                  >
                    <div className="text-center p-4">
                      <FileImage className="w-12 h-12 mx-auto text-muted-foreground/30 mb-2" />
                      <span className="text-xs text-muted-foreground">
                        {canonicalDoc.filename} ({canonicalDoc.metadata.width} × {canonicalDoc.metadata.height}px)
                      </span>
                    </div>

                    {/* Overlay Bounding Boxes */}
                    {filteredRegions.map((region) => {
                      const [ymin, xmin, ymax, xmax] = region.bounding_box;
                      const top = `${ymin * 100}%`;
                      const left = `${xmin * 100}%`;
                      const width = `${(xmax - xmin) * 100}%`;
                      const height = `${(ymax - ymin) * 100}%`;

                      const isSelected = selectedRegion?.region_id === region.region_id;

                      let borderColor = "border-sky-500 bg-sky-500/10";
                      if (region.region_type === "text") borderColor = "border-emerald-500 bg-emerald-500/10";
                      if (region.region_type === "diagram") borderColor = "border-purple-500 bg-purple-500/10";
                      if (region.region_type === "chart") borderColor = "border-amber-500 bg-amber-500/10";

                      return (
                        <div
                          key={region.region_id}
                          onClick={() => setSelectedRegion(region)}
                          className={`absolute border-2 cursor-pointer transition-all rounded-xs hover:z-20 hover:scale-[1.01] ${borderColor} ${
                            isSelected ? "ring-2 ring-primary ring-offset-1 z-30" : "z-10"
                          }`}
                          style={{ top, left, width, height }}
                          title={`${region.label} (${Math.round(region.confidence * 100)}%)`}
                        >
                          <span className="absolute -top-4 left-0 px-1 py-0.2 text-[9px] font-bold text-white bg-foreground/80 rounded-xs truncate max-w-[120px]">
                            {region.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Region Inspector Card */}
                <div className="p-5 bg-card border border-border rounded-xl space-y-4">
                  <h3 className="text-sm font-bold text-foreground flex items-center space-x-1.5">
                    <Layers className="w-4 h-4 text-primary" />
                    <span>Selected Region Properties</span>
                  </h3>

                  {selectedRegion ? (
                    <div className="space-y-3 text-xs">
                      <div>
                        <span className="text-muted-foreground">Region ID:</span>
                        <div className="font-mono font-medium text-foreground">{selectedRegion.region_id}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Label:</span>
                        <div className="font-semibold text-foreground capitalize">{selectedRegion.label}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Type:</span>
                        <div className="capitalize">{selectedRegion.region_type}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Confidence:</span>
                        <div className="font-semibold text-emerald-600">
                          {Math.round(selectedRegion.confidence * 100)}%
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Provenance:</span>
                        <div className="font-mono">{selectedRegion.provenance}</div>
                      </div>
                      {selectedRegion.text && (
                        <div>
                          <span className="text-muted-foreground">Recognized Text:</span>
                          <div className="p-2 bg-muted rounded font-mono mt-1 text-foreground">
                            {selectedRegion.text}
                          </div>
                        </div>
                      )}
                      <div>
                        <span className="text-muted-foreground">Normalized Bounds [ymin, xmin, ymax, xmax]:</span>
                        <div className="font-mono text-[11px] text-muted-foreground mt-0.5">
                          {JSON.stringify(selectedRegion.bounding_box)}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-10 text-muted-foreground">
                      <Eye className="w-8 h-8 mx-auto mb-2 opacity-40" />
                      <p>Click any bounding box on the image canvas to inspect its metadata and extracted text.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: OCR Text Layer */}
          {activeTab === "ocr" && (
            <div className="p-5 bg-card border border-border rounded-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center space-x-2">
                  <Type className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-bold text-foreground">Recognized Text Stream</h3>
                </div>
                <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                  <span>Words: <strong>{canonicalDoc.analysis.ocr_word_count}</strong></span>
                  <span>Confidence: <strong>{Math.round(canonicalDoc.analysis.ocr_average_confidence * 100)}%</strong></span>
                </div>
              </div>

              {canonicalDoc.analysis.ocr_full_text ? (
                <div className="p-4 bg-muted/50 rounded-lg font-mono text-sm leading-relaxed whitespace-pre-wrap text-foreground">
                  {canonicalDoc.analysis.ocr_full_text}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-6 text-center">
                  No textual characters recognized in this image.
                </p>
              )}
            </div>
          )}

          {/* TAB 3: Diagrams & Charts */}
          {activeTab === "insights" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Diagram Analysis */}
              <div className="p-5 bg-card border border-border rounded-xl space-y-4">
                <div className="flex items-center space-x-2">
                  <GitBranch className="w-5 h-5 text-purple-500" />
                  <h3 className="text-base font-bold text-foreground">Flowchart & Diagram Topology</h3>
                </div>

                {canonicalDoc.analysis.diagram.is_diagram ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-border pb-2">
                      <span className="text-muted-foreground">Diagram Type:</span>
                      <span className="font-semibold text-foreground capitalize">
                        {canonicalDoc.analysis.diagram.diagram_type}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-border pb-2">
                      <span className="text-muted-foreground">Flow Direction:</span>
                      <span className="font-semibold text-foreground capitalize">
                        {canonicalDoc.analysis.diagram.flow_direction}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-border pb-2">
                      <span className="text-muted-foreground">Nodes Identified:</span>
                      <span className="font-semibold text-foreground">
                        {canonicalDoc.analysis.diagram.nodes.length}
                      </span>
                    </div>

                    <div className="pt-2">
                      <span className="text-xs font-semibold text-muted-foreground">Diagram Nodes:</span>
                      <div className="mt-2 space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {canonicalDoc.analysis.diagram.nodes.map((node, i) => (
                          <div key={i} className="flex items-center space-x-2 p-2 bg-muted/60 rounded text-xs">
                            <ChevronRight className="w-3 h-3 text-purple-500" />
                            <span className="font-medium text-foreground">{node.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-8 text-center">
                    No flowchart or technical schematic detected in this image.
                  </p>
                )}
              </div>

              {/* Chart Analysis */}
              <div className="p-5 bg-card border border-border rounded-xl space-y-4">
                <div className="flex items-center space-x-2">
                  <BarChart2 className="w-5 h-5 text-amber-500" />
                  <h3 className="text-base font-bold text-foreground">Statistical Chart & Series</h3>
                </div>

                {canonicalDoc.analysis.chart.is_chart ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-border pb-2">
                      <span className="text-muted-foreground">Chart Type:</span>
                      <span className="font-semibold text-foreground capitalize">
                        {canonicalDoc.analysis.chart.chart_type}
                      </span>
                    </div>
                    {canonicalDoc.analysis.chart.title && (
                      <div className="flex justify-between border-b border-border pb-2">
                        <span className="text-muted-foreground">Title:</span>
                        <span className="font-semibold text-foreground">
                          {canonicalDoc.analysis.chart.title}
                        </span>
                      </div>
                    )}

                    <div className="pt-2">
                      <span className="text-xs font-semibold text-muted-foreground">Data Points / Series:</span>
                      <div className="mt-2 space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {canonicalDoc.analysis.chart.series_data.map((item, i) => (
                          <div key={i} className="flex justify-between p-2 bg-muted/60 rounded text-xs">
                            <span className="text-foreground">{item.label}</span>
                            <span className="font-bold text-foreground">
                              {item.value} {item.unit || ""}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-8 text-center">
                    No statistical data chart recognized in this image.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: Visual Question Answering (VQA) */}
          {activeTab === "vqa" && (
            <div className="p-5 bg-card border border-border rounded-xl space-y-6">
              <div className="space-y-1">
                <h3 className="text-base font-bold text-foreground flex items-center space-x-2">
                  <Bot className="w-5 h-5 text-primary" />
                  <span>Grounded Visual Question Answering</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Ask natural language questions grounded in the image content, OCR words, flowcharts, or charts.
                </p>
              </div>

              {/* Input Form */}
              <form onSubmit={handleAskQuestion} className="flex gap-2">
                <input
                  type="text"
                  value={vqaQuestion}
                  onChange={(e) => setVqaQuestion(e.target.value)}
                  placeholder="e.g. What text is written? What is the chart trend? Describe the diagram."
                  className="flex-1 px-4 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                />
                <button
                  type="submit"
                  disabled={vqaLoading || !vqaQuestion.trim()}
                  className="px-5 py-2 text-sm font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center space-x-1.5"
                >
                  {vqaLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                  <span>Ask</span>
                </button>
              </form>

              {/* QA History */}
              <div className="space-y-4">
                {vqaHistory.map((qa, idx) => (
                  <div key={idx} className="p-4 bg-muted/40 border border-border rounded-lg space-y-2 text-sm">
                    <div className="font-semibold text-foreground flex items-center space-x-2">
                      <span className="text-primary font-bold">Q:</span>
                      <span>{qa.question}</span>
                    </div>
                    <div className="text-foreground pl-5 border-l-2 border-primary/40">
                      <p>{qa.answer}</p>
                      {qa.reasoning && (
                        <p className="text-xs text-muted-foreground mt-1 italic">
                          Grounding: {qa.reasoning} (Confidence: {Math.round(qa.confidence * 100)}%)
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: Canonical JSON */}
          {activeTab === "json" && (
            <div className="p-5 bg-card border border-border rounded-xl">
              <pre className="p-4 bg-muted/60 rounded-lg text-xs font-mono overflow-x-auto max-h-[500px] text-foreground">
                {JSON.stringify(canonicalDoc, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
