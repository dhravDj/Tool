import React, { useState, useEffect } from "react";
import {
  ArchiveDocument,
  ArchiveAnalysisOverview,
  ArchiveEntry,
  ArchiveHierarchyNode,
  ArchiveSafetyReport,
} from "../types/api";
import { api } from "../services/api";

interface ArchiveIntelligenceViewProps {
  fileId: string;
  filename: string;
  onClose?: () => void;
  onOpenFile?: (childFileId: string) => void;
}

export const ArchiveIntelligenceView: React.FC<ArchiveIntelligenceViewProps> = ({
  fileId,
  filename,
  onClose,
  onOpenFile,
}) => {
  const [activeTab, setActiveTab] = useState<
    "overview" | "tree" | "entries" | "extraction" | "security" | "exports"
  >("overview");
  const [document, setDocument] = useState<ArchiveDocument | null>(null);
  const [overview, setOverview] = useState<ArchiveAnalysisOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [processing, setProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Tree & search state
  const [treeSearch, setTreeSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedEntry, setSelectedEntry] = useState<ArchiveEntry | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({ root: true });

  // Processing controls
  const [selectedMode, setSelectedMode] = useState<
    "inspect_only" | "extract_only" | "extract_and_analyze" | "selective"
  >("extract_and_analyze");
  const [passwordInput, setPasswordInput] = useState<string>("");
  const [selectedEntryIds, setSelectedEntryIds] = useState<string[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [docRes, ovRes] = await Promise.all([
          api.getArchiveDocumentResult(fileId).catch(() => null),
          api.getArchiveAnalysis(fileId).catch(() => null),
        ]);
        if (isMounted) {
          if (docRes) {
            setDocument(docRes);
            if (docRes.entries && docRes.entries.length > 0) {
              setSelectedEntry(docRes.entries[0]);
            }
          }
          setOverview(ovRes);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load archive intelligence data");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [fileId]);

  const handleRunProcessing = async () => {
    setProcessing(true);
    setError(null);
    try {
      const doc = await api.analyzeArchiveFile(fileId, {
        mode: selectedMode,
        password: passwordInput || undefined,
        selected_entry_ids: selectedMode === "selective" ? selectedEntryIds : undefined,
      });
      setDocument(doc);
      const ovRes = await api.getArchiveAnalysis(fileId).catch(() => null);
      setOverview(ovRes);
      if (doc.entries && doc.entries.length > 0) {
        setSelectedEntry(doc.entries[0]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Archive processing failed");
    } finally {
      setProcessing(false);
    }
  };

  const toggleExpand = (nodeId: string) => {
    setExpandedNodes(prev => ({ ...prev, [nodeId]: !prev[nodeId] }));
  };

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // Filter entries
  const filteredEntries = (document?.entries || []).filter(e => {
    if (typeFilter !== "all" && e.detection_result?.category !== typeFilter) return false;
    if (statusFilter !== "all" && e.processing_status !== statusFilter) return false;
    if (treeSearch.trim()) {
      const q = treeSearch.toLowerCase();
      return e.filename.toLowerCase().includes(q) || e.original_path.toLowerCase().includes(q);
    }
    return true;
  });

  const toggleEntrySelection = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedEntryIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // Render tree node recursive
  const renderTreeNode = (node: ArchiveHierarchyNode, depth = 0) => {
    const isExpanded = expandedNodes[node.id] ?? false;
    const isMatch =
      !treeSearch.trim() ||
      node.name.toLowerCase().includes(treeSearch.toLowerCase()) ||
      node.path.toLowerCase().includes(treeSearch.toLowerCase());

    if (!isMatch && !node.is_directory) return null;

    return (
      <div key={node.id} className="select-none" style={{ marginLeft: `${depth * 16}px` }}>
        <div
          className={`flex items-center gap-2 py-1 px-2 rounded cursor-pointer hover:bg-slate-100 transition-colors ${
            selectedEntry?.entry_id === node.entry_id ? "bg-blue-50 text-blue-700 font-medium" : "text-slate-700"
          }`}
          onClick={() => {
            if (node.is_directory) {
              toggleExpand(node.id);
            } else if (node.entry_id && document?.entries) {
              const matched = document.entries.find(e => e.entry_id === node.entry_id);
              if (matched) setSelectedEntry(matched);
            }
          }}
        >
          {node.is_directory ? (
            <span className="text-amber-500 font-bold text-sm">
              {isExpanded ? "📂" : "📁"}
            </span>
          ) : node.is_nested_archive ? (
            <span className="text-purple-600 font-bold text-sm">📦</span>
          ) : (
            <span className="text-slate-400 text-sm">📄</span>
          )}

          <span className="text-sm truncate flex-1">{node.name}</span>

          {node.is_nested_archive && (
            <span className="text-[10px] font-semibold bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
              NESTED
            </span>
          )}

          <span className="text-xs text-slate-400">
            {node.is_directory ? `${node.file_count} files` : formatBytes(node.total_size)}
          </span>
        </div>

        {node.is_directory && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-lg shadow-sm border border-slate-200">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-slate-600 font-medium">Loading archive inspection data...</p>
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <h3 className="font-bold text-lg mb-2">Error Loading Archive Intelligence</h3>
        <p className="text-sm mb-4">{error}</p>
        <button
          onClick={handleRunProcessing}
          disabled={processing}
          className="px-4 py-2 bg-red-600 text-white rounded font-medium hover:bg-red-700 transition"
        >
          {processing ? "Processing..." : "Retry Inspection"}
        </button>
      </div>
    );
  }

  const meta = document?.metadata || (overview ? {
    file_count: overview.file_count,
    directory_count: overview.directory_count,
    total_uncompressed_size: overview.total_uncompressed_size,
    compression_ratio: overview.compression_ratio,
  } : {});
  const safety: ArchiveSafetyReport = document?.safety_report || {
    path_traversal_blocked: 0,
    symlink_entries_blocked: 0,
    suspicious_entries: 0,
    size_limit_exceeded: false,
    compression_ratio_exceeded: false,
    entry_limit_exceeded: false,
    nesting_limit_exceeded: false,
    timeout_exceeded: false,
    encryption_detected: false,
    corruption_detected: false,
    blocked_entry_count: 0,
    warnings: [],
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden flex flex-col h-full max-h-[92vh]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📦</span>
            <h2 className="text-xl font-bold text-slate-800">{filename}</h2>
            <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
              {document?.archive_format || "ARCHIVE"}
            </span>
            <span
              className={`text-xs uppercase font-bold px-2 py-0.5 rounded ${
                document?.processing_status === "completed"
                  ? "bg-green-100 text-green-700"
                  : document?.processing_status === "partial"
                  ? "bg-amber-100 text-amber-700"
                  : document?.processing_status === "blocked"
                  ? "bg-red-100 text-red-700"
                  : "bg-slate-200 text-slate-700"
              }`}
            >
              {document?.processing_status || "INSPECTED"}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {document?.total_entry_count ?? 0} entries • {formatBytes(document?.extracted_size || 0)} extracted • Compression ratio: {meta.compression_ratio ?? 1}:1
          </p>
        </div>

        <div className="flex items-center gap-2">
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200 transition"
              title="Close view"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Security alert banner if issues detected */}
      {(safety.path_traversal_blocked > 0 ||
        safety.symlink_entries_blocked > 0 ||
        safety.compression_ratio_exceeded ||
        safety.encryption_detected) && (
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center justify-between text-xs text-amber-900">
          <div className="flex items-center gap-2 font-medium">
            <span>⚠️</span>
            <span>
              Security notice:{" "}
              {safety.path_traversal_blocked > 0 && `${safety.path_traversal_blocked} path traversals blocked. `}
              {safety.symlink_entries_blocked > 0 && `${safety.symlink_entries_blocked} symlink escapes blocked. `}
              {safety.compression_ratio_exceeded && "Archive bomb compression ratio exceeded. "}
              {safety.encryption_detected && "Password encryption detected. "}
            </span>
          </div>
          <button
            onClick={() => setActiveTab("security")}
            className="text-amber-800 underline font-semibold hover:text-amber-950"
          >
            View Security Audit
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-6">
        {[
          { key: "overview", label: "Overview", icon: "📊" },
          { key: "tree", label: "Hierarchy Tree", icon: "🌲" },
          { key: "entries", label: "Entries Manifest", icon: "📋" },
          { key: "extraction", label: "Extraction Results", icon: "📂" },
          { key: "security", label: "Security Audit", icon: "🛡️" },
          { key: "exports", label: "Downloads & Exports", icon: "💾" },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`py-3 px-4 text-sm font-medium border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === tab.key
                ? "border-blue-600 text-blue-600 bg-blue-50/50"
                : "border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300"
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
        {/* 1. OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase">Archive Format</span>
                <p className="text-2xl font-bold text-slate-800 mt-1 uppercase">
                  {document?.archive_format || "ZIP"}
                </p>
                <span className="text-xs text-slate-400">
                  Compressed: {formatBytes(meta.file_size || 0)}
                </span>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase">Total Entries</span>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {document?.total_entry_count || 0}
                </p>
                <span className="text-xs text-slate-400">
                  {meta.file_count || 0} files / {meta.directory_count || 0} folders
                </span>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase">Uncompressed Size</span>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {formatBytes(meta.total_uncompressed_size || 0)}
                </p>
                <span className="text-xs text-slate-400">
                  Ratio: {meta.compression_ratio ?? 1}:1
                </span>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase">Extracted Files</span>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {document?.extracted_files?.length || 0}
                </p>
                <span className="text-xs text-slate-400">
                  {document?.nested_archives?.length || 0} nested archives
                </span>
              </div>
            </div>

            {/* Processing Controls Panel */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
                <span>⚙️</span> Processing & Extraction Controls
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Processing Mode
                  </label>
                  <select
                    value={selectedMode}
                    onChange={e => setSelectedMode(e.target.value as any)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white text-slate-700"
                  >
                    <option value="inspect_only">Mode A: Inspect Only (Metadata/Tree)</option>
                    <option value="extract_only">Mode B: Extract Only (Isolated Files)</option>
                    <option value="extract_and_analyze">Mode C: Extract & Analyze (Downstream AI)</option>
                    <option value="selective">Mode D: Selective Extraction</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Decryption Password (if required)
                  </label>
                  <input
                    type="password"
                    placeholder="Enter password..."
                    value={passwordInput}
                    onChange={e => setPasswordInput(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white text-slate-700"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={handleRunProcessing}
                    disabled={processing}
                    className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {processing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Processing Archive...</span>
                      </>
                    ) : (
                      <>
                        <span>▶</span>
                        <span>Start Processing</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {selectedMode === "extract_and_analyze" && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
                  ℹ️ <strong>Mode C Notice:</strong> Extracted documents, images, spreadsheets, code, and nested archives will be registered and routed automatically to their respective DocuMind AI intelligence engines.
                </div>
              )}
            </div>

            {/* Archive Comment or Description */}
            {meta.comment && (
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase">Archive Comment</span>
                <pre className="text-sm font-mono text-slate-700 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-100 whitespace-pre-wrap">
                  {meta.comment}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* 2. HIERARCHY TREE TAB */}
        {activeTab === "tree" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
            {/* Tree Navigator */}
            <div className="md:col-span-2 bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col h-[650px]">
              <div className="flex items-center gap-2 mb-3">
                <input
                  type="text"
                  placeholder="Search files in tree..."
                  value={treeSearch}
                  onChange={e => setTreeSearch(e.target.value)}
                  className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-1.5"
                />
                <button
                  onClick={() => setExpandedNodes({ root: true })}
                  className="text-xs px-2.5 py-1.5 border border-slate-300 rounded hover:bg-slate-50 text-slate-600"
                >
                  Collapse
                </button>
              </div>

              <div className="flex-1 overflow-y-auto border border-slate-100 p-2 rounded-lg bg-slate-50/50">
                {document?.hierarchy ? (
                  renderTreeNode(document.hierarchy)
                ) : (
                  <p className="text-sm text-slate-400 p-4">No directory tree available.</p>
                )}
              </div>
            </div>

            {/* Entry Inspector Panel */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
              <h3 className="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">
                🔍 Entry Inspector
              </h3>

              {selectedEntry ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-0.5">Filename</span>
                    <span className="font-semibold text-slate-800 break-all">{selectedEntry.filename}</span>
                  </div>

                  <div>
                    <span className="text-slate-400 block mb-0.5">Original Archive Path</span>
                    <span className="font-mono text-slate-700 break-all bg-slate-50 p-1.5 rounded block border border-slate-100">
                      {selectedEntry.original_path}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block mb-0.5">Normalized Path</span>
                    <span className="font-mono text-slate-700 break-all">{selectedEntry.normalized_path}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                    <div>
                      <span className="text-slate-400 block mb-0.5">Uncompressed</span>
                      <span className="font-medium text-slate-700">{formatBytes(selectedEntry.uncompressed_size)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block mb-0.5">Compressed</span>
                      <span className="font-medium text-slate-700">{formatBytes(selectedEntry.compressed_size)}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-slate-400 block mb-0.5">Compression</span>
                      <span className="font-medium text-slate-700">{selectedEntry.compression_method || "None"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block mb-0.5">Checksum</span>
                      <span className="font-mono text-slate-700">{selectedEntry.checksum || "N/A"}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-slate-400 block mb-0.5">Detected Format / Category</span>
                    <span className="inline-block px-2 py-0.5 bg-blue-50 text-blue-700 rounded font-semibold text-[11px]">
                      {selectedEntry.detection_result?.canonical_name || "Unknown"} ({selectedEntry.detection_result?.category || "unknown"})
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block mb-0.5">Processing Status</span>
                    <span
                      className={`inline-block px-2 py-0.5 rounded font-semibold text-[11px] uppercase ${
                        selectedEntry.processing_status === "extracted"
                          ? "bg-green-100 text-green-700"
                          : selectedEntry.processing_status === "blocked"
                          ? "bg-red-100 text-red-700"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {selectedEntry.processing_status}
                    </span>
                  </div>

                  {selectedEntry.error && (
                    <div className="p-2 bg-red-50 text-red-700 rounded border border-red-200">
                      <strong>Error:</strong> {selectedEntry.error}
                    </div>
                  )}

                  {selectedEntry.extracted_file_id && onOpenFile && (
                    <div className="pt-4">
                      <button
                        onClick={() => onOpenFile(selectedEntry.extracted_file_id!)}
                        className="w-full py-1.5 px-3 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 transition"
                      >
                        Open Extracted File
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Select an entry from the tree to view its inspection details.</p>
              )}
            </div>
          </div>
        )}

        {/* 3. ENTRIES MANIFEST TAB */}
        {activeTab === "entries" && (
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between gap-4 mb-4">
              <input
                type="text"
                placeholder="Search entries..."
                value={treeSearch}
                onChange={e => setTreeSearch(e.target.value)}
                className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 w-64"
              />

              <div className="flex items-center gap-2">
                <select
                  value={typeFilter}
                  onChange={e => setTypeFilter(e.target.value)}
                  className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700"
                >
                  <option value="all">All Categories</option>
                  <option value="document">Documents</option>
                  <option value="image">Images</option>
                  <option value="spreadsheet">Spreadsheets</option>
                  <option value="code">Code</option>
                  <option value="structured_data">Structured Data</option>
                  <option value="archive">Archives</option>
                </select>

                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700"
                >
                  <option value="all">All Statuses</option>
                  <option value="inspected">Inspected</option>
                  <option value="extracted">Extracted</option>
                  <option value="blocked">Blocked</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50">
                    <th className="py-2.5 px-3 w-8">
                      <span className="sr-only">Select</span>
                    </th>
                    <th className="py-2.5 px-3">Path</th>
                    <th className="py-2.5 px-3">Size</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Encrypted</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredEntries.map(e => (
                    <tr
                      key={e.entry_id}
                      onClick={() => setSelectedEntry(e)}
                      className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                        selectedEntryIds.includes(e.entry_id) ? "bg-blue-50/40" : ""
                      }`}
                    >
                      <td className="py-2 px-3 w-8" onClick={ev => toggleEntrySelection(e.entry_id, ev)}>
                        <input
                          type="checkbox"
                          checked={selectedEntryIds.includes(e.entry_id)}
                          onChange={() => {}}
                          className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="py-2 px-3 font-mono text-slate-700">{e.original_path}</td>
                      <td className="py-2 px-3">{formatBytes(e.uncompressed_size)}</td>
                      <td className="py-2 px-3">
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">
                          {e.detection_result?.category || "file"}
                        </span>
                      </td>
                      <td className="py-2 px-3">{e.encrypted ? "🔒 Yes" : "No"}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-1.5 py-0.5 rounded font-semibold uppercase text-[10px] ${
                            e.processing_status === "extracted"
                              ? "bg-green-100 text-green-700"
                              : e.processing_status === "blocked"
                              ? "bg-red-100 text-red-700"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {e.processing_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 4. EXTRACTION RESULTS TAB */}
        {activeTab === "extraction" && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-base text-slate-800 mb-3">Extracted Files & Downstream Routing</h3>
              {document?.extracted_files && document.extracted_files.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50">
                        <th className="py-2.5 px-3">Path</th>
                        <th className="py-2.5 px-3">Size</th>
                        <th className="py-2.5 px-3">SHA256</th>
                        <th className="py-2.5 px-3">Downstream Engine</th>
                        <th className="py-2.5 px-3">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {document.extracted_files.map((f, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-mono text-slate-700">{f.original_path}</td>
                          <td className="py-2 px-3">{formatBytes(f.file_size)}</td>
                          <td className="py-2 px-3 font-mono text-[11px] text-slate-500">
                            {f.sha256 ? `${f.sha256.substring(0, 12)}...` : "N/A"}
                          </td>
                          <td className="py-2 px-3">
                            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 font-medium rounded">
                              {f.downstream_engine || "Stored"}
                            </span>
                          </td>
                          <td className="py-2 px-3">
                            {f.created_file_id && onOpenFile && (
                              <button
                                onClick={() => onOpenFile(f.created_file_id)}
                                className="text-blue-600 hover:text-blue-800 font-medium text-xs underline"
                              >
                                View
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-400 py-4">No files extracted yet. Run Mode B or C to extract files.</p>
              )}
            </div>
          </div>
        )}

        {/* 5. SECURITY AUDIT TAB */}
        {activeTab === "security" && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-base text-slate-800 mb-4 flex items-center gap-2">
                <span>🛡️</span> Security & Vulnerability Assessment
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-500 text-xs block mb-1">Path Traversals Blocked</span>
                  <span className={`text-xl font-bold ${safety.path_traversal_blocked > 0 ? "text-red-600" : "text-green-600"}`}>
                    {safety.path_traversal_blocked}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-500 text-xs block mb-1">Symlinks Blocked</span>
                  <span className={`text-xl font-bold ${safety.symlink_entries_blocked > 0 ? "text-amber-600" : "text-green-600"}`}>
                    {safety.symlink_entries_blocked}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-500 text-xs block mb-1">Suspicious Device Files</span>
                  <span className={`text-xl font-bold ${safety.suspicious_entries > 0 ? "text-red-600" : "text-green-600"}`}>
                    {safety.suspicious_entries}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-500 text-xs block mb-1">Archive Bomb Flag</span>
                  <span className={`text-xl font-bold ${safety.compression_ratio_exceeded ? "text-red-600" : "text-green-600"}`}>
                    {safety.compression_ratio_exceeded ? "TRIGGERED" : "CLEAN"}
                  </span>
                </div>
              </div>

              {/* Blocked Entries Table */}
              {document?.blocked_entries && document.blocked_entries.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-semibold text-sm text-slate-700 mb-2">Blocked Malicious Entries</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-red-200 text-red-600 bg-red-50">
                          <th className="py-2 px-3">Path</th>
                          <th className="py-2 px-3">Reason</th>
                          <th className="py-2 px-3">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-100">
                        {document.blocked_entries.map((b, i) => (
                          <tr key={i} className="bg-red-50/30">
                            <td className="py-2 px-3 font-mono text-red-800">{b.original_path}</td>
                            <td className="py-2 px-3 text-red-700">{b.reason}</td>
                            <td className="py-2 px-3 font-bold text-red-600">BLOCKED</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Warnings List */}
              {safety.warnings && safety.warnings.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm text-slate-700 mb-2">Security Warnings & Notices</h4>
                  <ul className="space-y-1 text-xs text-slate-600 list-disc pl-5">
                    {safety.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. EXPORTS TAB */}
        {activeTab === "exports" && (
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-base text-slate-800 mb-4 flex items-center gap-2">
              <span>💾</span> Download Artifacts & Reports
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { format: "json", title: "Archive Document JSON", desc: "Full canonical archive document specification", icon: "📄" },
                { format: "markdown", title: "Archive Markdown Report", desc: "Human-readable GitHub-flavored Markdown overview", icon: "📝" },
                { format: "text", title: "Plain Text Summary", desc: "Lightweight ASCII overview and hierarchy summary", icon: "📃" },
                { format: "manifest", title: "Archive Entry Manifest", desc: "Comprehensive table of all contained files and checksums", icon: "📊" },
                { format: "tree", title: "Directory Hierarchy Tree", desc: "Visual ASCII folder hierarchy diagram", icon: "🌲" },
                { format: "extraction_report", title: "Extraction Metrics Report", desc: "Detailed breakdown of extracted, blocked, and failed files", icon: "📈" },
                { format: "security_report", title: "Security Assessment Report", desc: "Defense audit: path traversal, bomb ratio, symlink checks", icon: "🛡️" },
                { format: "child_manifest", title: "Child Files Manifest", desc: "Provenance linkage and storage IDs for extracted files", icon: "🔗" },
              ].map(exp => (
                <div key={exp.format} className="p-4 rounded-lg border border-slate-200 flex items-center justify-between hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{exp.icon}</span>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800">{exp.title}</h4>
                      <p className="text-xs text-slate-500">{exp.desc}</p>
                    </div>
                  </div>
                  <a
                    href={api.getArchiveExportUrl(fileId, exp.format)}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-slate-100 text-slate-700 font-medium text-xs rounded hover:bg-slate-200 transition"
                  >
                    Download
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
