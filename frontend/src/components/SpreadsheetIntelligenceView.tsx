/** Spreadsheet Intelligence View Component for DocuMind AI. */

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  BarChart2,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  EyeOff,
  FileSpreadsheet,
  FileText,
  Key,
  Layers,
  Loader2,
  Search,
  Sparkles,
  Table as TableIcon,
} from "lucide-react";
import { api } from "@/services/api";
import {
  CellData,
  SpreadsheetDocument,
  SpreadsheetManifest,
  WorksheetData,
} from "@/types/api";

interface SpreadsheetIntelligenceViewProps {
  fileId: string;
  filename: string;
  format?: string;
}

export const SpreadsheetIntelligenceView: React.FC<SpreadsheetIntelligenceViewProps> = ({
  fileId,
  filename,
  format = "spreadsheet",
}) => {
  const [statusLoading, setStatusLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [canonicalDoc, setCanonicalDoc] = useState<SpreadsheetDocument | null>(null);
  const [_manifest, setManifest] = useState<SpreadsheetManifest | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Active worksheet & tab state
  const [activeSheetId, setActiveSheetId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"grid" | "profiling" | "formulas" | "tables_charts" | "json">("grid");

  // Grid pagination and search
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 50;
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  const fetchSpreadsheetData = async () => {
    setStatusLoading(true);
    setErrorMessage(null);
    try {
      const doc = await api.getCanonicalSpreadsheetDocument(fileId);
      setCanonicalDoc(doc);
      if (doc.worksheets.length > 0 && !activeSheetId) {
        setActiveSheetId(doc.worksheets[0].sheet_id);
      }
      try {
        const m = await api.getSpreadsheetManifest(fileId);
        setManifest(m);
      } catch {
        // Manifest optional
      }
    } catch {
      setCanonicalDoc(null);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchSpreadsheetData();
  }, [fileId]);

  const handleRunAnalysis = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.analyzeSpreadsheet(fileId);
      await fetchSpreadsheetData();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to analyze spreadsheet.");
    } finally {
      setActionLoading(false);
    }
  };

  // Find active worksheet
  const currentWorksheet: WorksheetData | undefined =
    canonicalDoc?.worksheets.find((ws) => ws.sheet_id === activeSheetId) ||
    canonicalDoc?.worksheets[0];

  // Filter rows based on search
  const filteredRows = (currentWorksheet?.rows || []).filter((row) => {
    if (!searchQuery.trim()) return true;
    return row.cells.some((cell) =>
      String(cell.formatted_value || cell.raw_value || "")
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
    );
  });

  // Paginated rows for display
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const paginatedRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  // Formulas list across active worksheet
  const worksheetFormulas: CellData[] = [];
  if (currentWorksheet) {
    for (const r of currentWorksheet.rows) {
      for (const c of r.cells) {
        if (c.formula) {
          worksheetFormulas.push(c);
        }
      }
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* 1. Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-white">{filename}</h2>
              <span className="px-2 py-0.5 text-xs font-medium uppercase rounded bg-slate-800 text-emerald-400 border border-emerald-500/30">
                {canonicalDoc?.workbook_metadata.format || format}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {canonicalDoc ? (
                <>
                  {canonicalDoc.worksheets.length} Sheet(s) •{" "}
                  {currentWorksheet?.total_rows.toLocaleString() || 0} Rows •{" "}
                  {currentWorksheet?.total_columns || 0} Cols •{" "}
                  {worksheetFormulas.length} Formulas
                </>
              ) : (
                "Spreadsheet Intelligence Engine"
              )}
            </p>
          </div>
        </div>

        {/* Download & Action Buttons */}
        <div className="flex items-center gap-2">
          {canonicalDoc && (
            <div className="flex items-center gap-1.5 mr-2">
              <a
                href={api.getSpreadsheetDownloadUrl(fileId, "json")}
                download
                className="px-2.5 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5 transition"
                title="Download full JSON representation"
              >
                <Download className="w-3.5 h-3.5" /> JSON
              </a>
              <a
                href={api.getSpreadsheetDownloadUrl(fileId, "markdown")}
                download
                className="px-2.5 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5 transition"
                title="Download Markdown report"
              >
                <FileText className="w-3.5 h-3.5" /> Markdown
              </a>
              <a
                href={api.getSpreadsheetDownloadUrl(fileId, "csv", currentWorksheet?.position || 1)}
                download
                className="px-2.5 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5 transition"
                title="Download CSV for current worksheet"
              >
                <TableIcon className="w-3.5 h-3.5" /> CSV
              </a>
              <a
                href={api.getSpreadsheetDownloadUrl(fileId, "xlsx")}
                download
                className="px-2.5 py-1.5 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-1.5 transition"
                title="Download reconstructed XLSX"
              >
                <Download className="w-3.5 h-3.5" /> XLSX
              </a>
            </div>
          )}

          <button
            onClick={handleRunAnalysis}
            disabled={actionLoading}
            className="px-3 py-1.5 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg flex items-center gap-1.5 transition shadow-lg shadow-emerald-600/20"
          >
            {actionLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            {canonicalDoc ? "Re-Analyze" : "Analyze Spreadsheet"}
          </button>
        </div>
      </div>

      {/* 2. Error Banner */}
      {errorMessage && (
        <div className="p-3 bg-red-500/10 border-b border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 3. Main Body */}
      {statusLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mb-3" />
          <p className="text-sm">Loading spreadsheet intelligence analysis...</p>
        </div>
      ) : !canonicalDoc ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-400">
          <div className="p-4 bg-slate-800/60 rounded-full mb-3 text-emerald-400">
            <FileSpreadsheet className="w-10 h-10" />
          </div>
          <h3 className="text-base font-semibold text-white mb-1">Spreadsheet Not Yet Analyzed</h3>
          <p className="text-xs text-slate-400 max-w-sm mb-4">
            Execute spreadsheet intelligence to extract formulas, formatting, merged cells,
            data quality summaries, and multi-sheet relationships.
          </p>
          <button
            onClick={handleRunAnalysis}
            disabled={actionLoading}
            className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2 transition"
          >
            {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Analyze Spreadsheet Now
          </button>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Sheet Selector Tabs */}
          <div className="flex items-center gap-1 px-4 py-2 bg-slate-950/60 border-b border-slate-800 overflow-x-auto">
            <span className="text-xs font-semibold text-slate-400 mr-2 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5" /> Sheets:
            </span>
            {canonicalDoc.worksheets.map((ws) => {
              const isSelected = ws.sheet_id === activeSheetId;
              const isHidden = ws.visibility !== "visible";
              return (
                <button
                  key={ws.sheet_id}
                  onClick={() => {
                    setActiveSheetId(ws.sheet_id);
                    setCurrentPage(1);
                    setSelectedCell(null);
                  }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg flex items-center gap-1.5 transition whitespace-nowrap ${
                    isSelected
                      ? "bg-emerald-600/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-slate-800/40 text-slate-300 hover:bg-slate-800 border border-slate-800"
                  }`}
                >
                  {isHidden ? (
                    <span title={`Visibility: ${ws.visibility}`}>
                      <EyeOff className="w-3 h-3 text-amber-400" />
                    </span>
                  ) : (
                    <Eye className="w-3 h-3 text-slate-400" />
                  )}
                  <span>{ws.name}</span>
                  {isHidden && (
                    <span className="px-1 py-0.2 text-[10px] uppercase font-bold text-amber-400 bg-amber-400/10 rounded">
                      {ws.visibility}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Subsystem Navigation Bar */}
          <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("grid")}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  activeTab === "grid"
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Grid View
              </button>
              <button
                onClick={() => setActiveTab("profiling")}
                className={`px-3 py-1 rounded-md font-medium transition flex items-center gap-1.5 ${
                  activeTab === "profiling"
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <BarChart2 className="w-3.5 h-3.5" />
                Data Profiling
              </button>
              <button
                onClick={() => setActiveTab("formulas")}
                className={`px-3 py-1 rounded-md font-medium transition flex items-center gap-1.5 ${
                  activeTab === "formulas"
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                Formulas ({worksheetFormulas.length})
              </button>
              <button
                onClick={() => setActiveTab("tables_charts")}
                className={`px-3 py-1 rounded-md font-medium transition flex items-center gap-1.5 ${
                  activeTab === "tables_charts"
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                Tables & Charts ({(currentWorksheet?.tables.length || 0) + (currentWorksheet?.charts.length || 0)})
              </button>
              <button
                onClick={() => setActiveTab("json")}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  activeTab === "json"
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                JSON
              </button>
            </div>

            {/* Search Input for Grid Tab */}
            {activeTab === "grid" && (
              <div className="relative w-56">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search worksheet cells..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}
          </div>

          {/* 4. Tab Content Panes */}
          <div className="flex-1 overflow-auto bg-slate-950 p-4">
            {/* A. GRID TAB */}
            {activeTab === "grid" && (
              <div className="flex flex-col h-full">
                {/* Active Cell Inspector Bar */}
                {selectedCell && (
                  <div className="mb-3 p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs flex flex-wrap items-center gap-4">
                    <span className="font-mono font-bold text-emerald-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {selectedCell.address}
                    </span>
                    <span className="text-slate-400">
                      Value: <strong className="text-white">{String(selectedCell.raw_value ?? "")}</strong>
                    </span>
                    {selectedCell.formula && (
                      <span className="text-emerald-400 font-mono">
                        Formula: <strong>{selectedCell.formula}</strong>
                      </span>
                    )}
                    {selectedCell.cached_value !== undefined && (
                      <span className="text-amber-400">
                        Cached: <strong>{String(selectedCell.cached_value)}</strong>
                      </span>
                    )}
                    <span className="text-slate-400">
                      Type: <span className="uppercase text-slate-200">{selectedCell.data_type}</span>
                    </span>
                    {selectedCell.style?.bold && <span className="font-bold text-slate-300">Bold</span>}
                    {selectedCell.style?.number_format && (
                      <span className="text-slate-400">Format: {selectedCell.style.number_format}</span>
                    )}
                  </div>
                )}

                {/* Table Viewport */}
                <div className="flex-1 overflow-auto border border-slate-800 rounded-lg bg-slate-900">
                  <table className="w-full text-left border-collapse text-xs font-mono">
                    <thead className="sticky top-0 bg-slate-800/95 backdrop-blur z-10 border-b border-slate-700">
                      <tr>
                        <th className="p-2 w-12 text-center text-slate-400 border-r border-slate-700 bg-slate-850">
                          #
                        </th>
                        {currentWorksheet?.columns.map((col) => (
                          <th
                            key={col.column_index}
                            className="p-2 min-w-[120px] max-w-[240px] text-slate-300 border-r border-slate-700 truncate"
                            title={`${col.name} (${col.column_letter})`}
                          >
                            <div className="font-semibold text-white truncate">{col.name}</div>
                            <div className="text-[10px] text-slate-400 flex items-center justify-between">
                              <span>{col.column_letter}</span>
                              {col.profiling && (
                                <span className="text-emerald-400 uppercase text-[9px]">
                                  {col.profiling.inferred_type}
                                </span>
                              )}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {paginatedRows.map((row) => {
                        const cellMap = new Map(row.cells.map((c) => [c.column, c]));
                        return (
                          <tr key={row.row_index} className="hover:bg-slate-800/50 transition">
                            <td className="p-2 text-center text-slate-500 border-r border-slate-800 bg-slate-900/60 font-semibold select-none">
                              {row.row_index}
                            </td>
                            {currentWorksheet?.columns.map((col) => {
                              const cell = cellMap.get(col.column_index);
                              const isSelected = selectedCell?.address === cell?.address;
                              const val = cell?.formatted_value ?? cell?.raw_value;

                              return (
                                <td
                                  key={col.column_index}
                                  onClick={() => cell && setSelectedCell(cell)}
                                  className={`p-2 border-r border-slate-800 truncate cursor-pointer transition ${
                                    isSelected
                                      ? "bg-emerald-500/20 text-emerald-200 outline outline-1 outline-emerald-500"
                                      : cell?.formula
                                      ? "bg-emerald-950/20 text-emerald-300"
                                      : "text-slate-300"
                                  } ${cell?.style?.bold ? "font-bold" : ""}`}
                                  title={cell?.formula ? `Formula: ${cell.formula}` : String(val ?? "")}
                                >
                                  {cell?.formula && (
                                    <span className="mr-1 text-[10px] text-emerald-400 font-bold select-none">
                                      fx
                                    </span>
                                  )}
                                  <span>{val !== null && val !== undefined ? String(val) : ""}</span>
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                <div className="flex items-center justify-between mt-3 text-xs text-slate-400">
                  <div>
                    Showing rows {(currentPage - 1) * pageSize + 1} to{" "}
                    {Math.min(currentPage * pageSize, filteredRows.length)} of {filteredRows.length.toLocaleString()}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage <= 1}
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" /> Prev
                    </button>
                    <span>
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage >= totalPages}
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                    >
                      Next <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* B. DATA PROFILING TAB */}
            {activeTab === "profiling" && (
              <div className="space-y-6">
                {currentWorksheet?.profiling && (
                  <>
                    {/* High-level stats cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Populated Cells</div>
                        <div className="text-xl font-bold text-white">
                          {currentWorksheet.profiling.populated_cells.toLocaleString()}
                        </div>
                      </div>
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Empty Rows</div>
                        <div className="text-xl font-bold text-white">
                          {currentWorksheet.profiling.empty_rows_count.toLocaleString()}
                        </div>
                      </div>
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Duplicate Rows</div>
                        <div className="text-xl font-bold text-amber-400">
                          {currentWorksheet.profiling.duplicate_rows_count.toLocaleString()}
                        </div>
                      </div>
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Merged Ranges</div>
                        <div className="text-xl font-bold text-emerald-400">
                          {currentWorksheet.merged_ranges.length}
                        </div>
                      </div>
                    </div>

                    {/* Candidate Primary Keys */}
                    {currentWorksheet.profiling.candidate_primary_keys.length > 0 && (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                        <Key className="w-4 h-4 flex-shrink-0" />
                        <span>
                          <strong>Candidate Primary Key(s):</strong>{" "}
                          {currentWorksheet.profiling.candidate_primary_keys.join(", ")}
                        </span>
                      </div>
                    )}

                    {/* Column Profiles Table */}
                    <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-800 text-slate-300 border-b border-slate-700">
                          <tr>
                            <th className="p-2.5">Column</th>
                            <th className="p-2.5">Inferred Type</th>
                            <th className="p-2.5 text-right">Nulls</th>
                            <th className="p-2.5 text-right">Unique</th>
                            <th className="p-2.5">Min</th>
                            <th className="p-2.5">Max</th>
                            <th className="p-2.5 text-right">Mean</th>
                            <th className="p-2.5 text-right">Std Dev</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 font-mono">
                          {currentWorksheet.profiling.column_profiles.map((cp) => (
                            <tr key={cp.column_index} className="hover:bg-slate-800/40">
                              <td className="p-2.5 font-sans font-semibold text-white">
                                {cp.column_name}{" "}
                                <span className="text-slate-400 font-mono text-[10px]">
                                  ({cp.column_letter})
                                </span>
                              </td>
                              <td className="p-2.5">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-emerald-400 border border-emerald-500/20">
                                  {cp.inferred_type}
                                </span>
                              </td>
                              <td className="p-2.5 text-right text-slate-400">{cp.null_count}</td>
                              <td className="p-2.5 text-right text-slate-200">{cp.unique_count}</td>
                              <td className="p-2.5 text-slate-300 truncate max-w-[120px]">
                                {cp.min_value !== null ? String(cp.min_value) : "-"}
                              </td>
                              <td className="p-2.5 text-slate-300 truncate max-w-[120px]">
                                {cp.max_value !== null ? String(cp.max_value) : "-"}
                              </td>
                              <td className="p-2.5 text-right text-slate-200">
                                {cp.mean !== null && cp.mean !== undefined ? cp.mean.toFixed(2) : "-"}
                              </td>
                              <td className="p-2.5 text-right text-slate-400">
                                {cp.std_dev !== null && cp.std_dev !== undefined ? cp.std_dev.toFixed(2) : "-"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* C. FORMULAS TAB */}
            {activeTab === "formulas" && (
              <div className="space-y-4">
                <div className="text-xs text-slate-400">
                  Showing {worksheetFormulas.length} formulas in worksheet{" "}
                  <strong>{currentWorksheet?.name}</strong>. Formulas are extracted statically without
                  automatic execution.
                </div>

                {worksheetFormulas.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-xs">
                    No formula expressions detected in this worksheet.
                  </div>
                ) : (
                  <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900 font-mono text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-slate-800 text-slate-300 border-b border-slate-700">
                        <tr>
                          <th className="p-2.5 w-24">Cell</th>
                          <th className="p-2.5">Formula Expression</th>
                          <th className="p-2.5">Cached Result</th>
                          <th className="p-2.5 w-28">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {worksheetFormulas.map((c) => (
                          <tr key={c.address} className="hover:bg-slate-800/40">
                            <td className="p-2.5 font-bold text-emerald-400">{c.address}</td>
                            <td className="p-2.5 text-slate-200 font-semibold">{c.formula}</td>
                            <td className="p-2.5 text-amber-300">
                              {c.cached_value !== undefined ? String(c.cached_value) : "N/A"}
                            </td>
                            <td className="p-2.5">
                              <button
                                onClick={() => {
                                  setSelectedCell(c);
                                  setActiveTab("grid");
                                }}
                                className="text-xs text-emerald-400 hover:underline font-sans"
                              >
                                View in Grid
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* D. TABLES & CHARTS TAB */}
            {activeTab === "tables_charts" && (
              <div className="space-y-6 text-xs">
                {/* Tables */}
                <div>
                  <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <TableIcon className="w-4 h-4 text-emerald-400" /> Embedded Excel Tables (
                    {currentWorksheet?.tables.length || 0})
                  </h4>
                  {(!currentWorksheet?.tables || currentWorksheet.tables.length === 0) ? (
                    <p className="text-slate-500">No structured Excel tables declared in this worksheet.</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentWorksheet.tables.map((t) => (
                        <div key={t.name} className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                          <div className="font-semibold text-white mb-1">{t.display_name}</div>
                          <div className="text-slate-400 mb-2">Range: <code className="text-emerald-400">{t.reference_range}</code></div>
                          <div className="text-slate-400">Columns: {t.columns.join(", ")}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Charts */}
                <div>
                  <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-emerald-400" /> Embedded Charts (
                    {currentWorksheet?.charts.length || 0})
                  </h4>
                  {(!currentWorksheet?.charts || currentWorksheet.charts.length === 0) ? (
                    <p className="text-slate-500">No chart objects embedded in this worksheet.</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentWorksheet.charts.map((ch, idx) => (
                        <div key={idx} className="p-4 bg-slate-900 border border-slate-800 rounded-lg">
                          <div className="font-semibold text-white mb-1">{ch.title || "Untitled Chart"}</div>
                          <div className="text-slate-400">Type: <span className="uppercase text-emerald-400">{ch.chart_type}</span></div>
                          <div className="text-slate-400">Data Series Count: {ch.series_count}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* E. JSON TAB */}
            {activeTab === "json" && (
              <pre className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-emerald-300 text-xs font-mono overflow-auto max-h-[600px]">
                {JSON.stringify(canonicalDoc, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
