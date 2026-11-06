import React, { useState, useEffect } from "react";
import {
  CodeDocument,
  CodeAnalysisOverview,
  CodeSymbol,
  CodeDiagnostic,
} from "../types/api";
import { api } from "../services/api";

interface CodeIntelligenceViewProps {
  fileId: string;
  filename: string;
  onClose?: () => void;
}

export const CodeIntelligenceView: React.FC<CodeIntelligenceViewProps> = ({
  fileId,
  filename,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<
    "overview" | "source" | "symbols" | "dependencies" | "metrics"
  >("overview");
  const [document, setDocument] = useState<CodeDocument | null>(null);
  const [overview, setOverview] = useState<CodeAnalysisOverview | null>(null);
  const [sourceCode, setSourceCode] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState<string>("");
  const [selectedDiagnostic, setSelectedDiagnostic] = useState<CodeDiagnostic | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [docRes, ovRes, srcRes] = await Promise.all([
          api.getCodeDocumentResult(fileId),
          api.getCodeAnalysis(fileId).catch(() => null),
          api.getCodeSource(fileId).catch(() => ""),
        ]);
        if (isMounted) {
          setDocument(docRes);
          setOverview(ovRes);
          setSourceCode(srcRes);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load code intelligence data");
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

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center bg-gray-50 rounded-lg p-6">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
          <p className="text-sm font-medium text-gray-600">Analyzing code structure & symbols...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="p-6 bg-red-50 text-red-700 rounded-lg">
        <p className="font-semibold">Error Loading Code Intelligence</p>
        <p className="text-sm mt-1">{error || "No document returned"}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="mt-4 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Close
          </button>
        )}
      </div>
    );
  }

  const filteredSymbols = document.symbols.filter((s: CodeSymbol) =>
    s.name.toLowerCase().includes(symbolFilter.toLowerCase()) ||
    s.symbol_type.toLowerCase().includes(symbolFilter.toLowerCase())
  );

  const lines = sourceCode.split("\n");

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          <span className="px-2.5 py-1 text-xs font-bold uppercase rounded bg-indigo-100 text-indigo-800">
            {document.language}
          </span>
          <div>
            <h2 className="text-lg font-bold text-gray-900">{filename}</h2>
            <p className="text-xs text-gray-500">
              {document.metrics.total_lines} lines • {document.symbols.length} symbols • {document.diagnostics.length} diagnostics
              {overview?.model_name ? ` • Engine: ${overview.model_name}` : ""}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative inline-block text-left">
            <a
              href={api.getCodeExportUrl(fileId, "json")}
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Export JSON
            </a>
            <a
              href={api.getCodeExportUrl(fileId, "markdown")}
              target="_blank"
              rel="noreferrer"
              className="ml-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Export Markdown
            </a>
            <a
              href={api.getCodeExportUrl(fileId, "txt")}
              target="_blank"
              rel="noreferrer"
              className="ml-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Export TXT
            </a>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded-md"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-6">
        {[
          { id: "overview", label: "Overview" },
          { id: "source", label: "Source & Diagnostics" },
          { id: "symbols", label: `Symbols (${document.symbols.length})` },
          { id: "dependencies", label: `Dependencies (${document.imports.length + document.dependencies.length})` },
          { id: "metrics", label: "Metrics & Complexity" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Metric KPI cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Lines of Code</span>
                <p className="text-2xl font-bold text-gray-900 mt-1">{document.metrics.code_lines}</p>
                <span className="text-xs text-gray-400">{document.metrics.total_lines} total lines</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Total Symbols</span>
                <p className="text-2xl font-bold text-indigo-600 mt-1">{document.symbols.length}</p>
                <span className="text-xs text-gray-400">
                  {document.metrics.class_count} classes, {document.metrics.function_count} functions
                </span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Cyclomatic Complexity</span>
                <p className="text-2xl font-bold text-amber-600 mt-1">{document.metrics.cyclomatic_complexity}</p>
                <span className="text-xs text-gray-400">Max nesting: {document.metrics.nesting_depth}</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Diagnostics</span>
                <p className={`text-2xl font-bold mt-1 ${document.diagnostics.length > 0 ? "text-red-600" : "text-emerald-600"}`}>
                  {document.diagnostics.length}
                </p>
                <span className="text-xs text-gray-400">
                  {document.syntax_validation.is_valid ? "Valid Syntax" : "Syntax Errors"}
                </span>
              </div>
            </div>

            {/* Syntax or Diagnostic Alerts */}
            {!document.syntax_validation.is_valid && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="text-sm font-semibold text-red-800">Syntax Errors Detected</h3>
                <ul className="mt-2 list-disc list-inside text-xs text-red-700 space-y-1">
                  {document.syntax_validation.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Diagnostics Summary */}
            {document.diagnostics.length > 0 && (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900">Diagnostics & Security Findings</h3>
                </div>
                <div className="divide-y divide-gray-100">
                  {document.diagnostics.map((diag) => (
                    <div
                      key={diag.diagnostic_id}
                      onClick={() => {
                        setSelectedDiagnostic(diag);
                        setActiveTab("source");
                      }}
                      className="p-3 hover:bg-gray-50 cursor-pointer flex items-start justify-between"
                    >
                      <div className="flex items-start space-x-2">
                        <span
                          className={`mt-0.5 px-2 py-0.5 text-xs font-semibold rounded uppercase ${
                            diag.severity === "error"
                              ? "bg-red-100 text-red-800"
                              : diag.severity === "warning"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {diag.severity}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{diag.message}</p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            Rule: {diag.rule_id} • Line {diag.start_line}, Col {diag.column}
                          </p>
                          {diag.suggested_remediation && (
                            <p className="text-xs text-indigo-600 mt-1">
                              💡 Fix: {diag.suggested_remediation}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-xs text-indigo-600 hover:underline">View in Source →</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "source" && (
          <div className="space-y-4">
            {selectedDiagnostic && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex justify-between items-center text-xs">
                <div>
                  <span className="font-semibold text-amber-800">Focused Diagnostic: </span>
                  <span className="text-amber-700">{selectedDiagnostic.message} (Line {selectedDiagnostic.start_line})</span>
                </div>
                <button
                  onClick={() => setSelectedDiagnostic(null)}
                  className="text-amber-800 font-bold ml-2"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="font-mono text-xs bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto max-h-[600px]">
              {lines.map((line, idx) => {
                const lineNo = idx + 1;
                const diag = document.diagnostics.find(
                  (d) => d.start_line <= lineNo && d.end_line >= lineNo
                );
                const isFocused = selectedDiagnostic && selectedDiagnostic.start_line === lineNo;

                return (
                  <div
                    key={lineNo}
                    className={`flex items-start hover:bg-gray-800/80 px-2 py-0.5 ${
                      isFocused
                        ? "bg-amber-900/50 border-l-4 border-amber-400"
                        : diag
                        ? diag.severity === "error"
                          ? "bg-red-950/40 border-l-2 border-red-500"
                          : "bg-amber-950/40 border-l-2 border-amber-500"
                        : ""
                    }`}
                  >
                    <span className="w-10 select-none text-right pr-4 text-gray-500">
                      {lineNo}
                    </span>
                    <pre className="flex-1 whitespace-pre">{line || " "}</pre>
                    {diag && (
                      <span
                        className="ml-2 px-1.5 py-0.2 rounded text-[10px] uppercase font-bold text-gray-300"
                        title={diag.message}
                      >
                        [{diag.rule_id}]
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === "symbols" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <input
                type="text"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                placeholder="Filter symbols by name or type..."
                className="w-72 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-indigo-500"
              />
              <span className="text-xs text-gray-500">
                Showing {filteredSymbols.length} of {document.symbols.length} symbols
              </span>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Symbol</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Lines</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Parameters</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Return</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {filteredSymbols.map((sym) => (
                    <tr key={sym.symbol_id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono font-medium text-indigo-700">
                        {sym.name}
                      </td>
                      <td className="px-4 py-2">
                        <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700 uppercase">
                          {sym.symbol_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-500 text-xs">
                        L{sym.start_line} - L{sym.end_line}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs text-gray-600">
                        {sym.parameters.length > 0 ? sym.parameters.join(", ") : "—"}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs text-gray-500">
                        {sym.return_type || "—"}
                      </td>
                    </tr>
                  ))}
                  {filteredSymbols.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                        No symbols match the current filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "dependencies" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Imports & Modules ({document.imports.length})
              </h3>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Module</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Statement</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Type</th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Line</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {document.imports.map((imp, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium font-mono text-gray-900">{imp.module_name}</td>
                        <td className="px-4 py-2 font-mono text-xs text-gray-600">{imp.statement}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-0.5 text-xs rounded ${
                              imp.is_external
                                ? "bg-amber-100 text-amber-800"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {imp.is_external ? "External" : "Internal"}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-xs text-gray-500">L{imp.line_number}</td>
                      </tr>
                    ))}
                    {document.imports.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                          No module imports detected.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Detected Dependencies ({document.dependencies.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {document.dependencies.map((dep, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="font-mono font-medium text-gray-900">{dep.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Type: <span className="capitalize">{dep.dependency_type}</span>
                    </p>
                  </div>
                ))}
                {document.dependencies.length === 0 && (
                  <p className="text-sm text-gray-500 col-span-3">No external third-party packages detected.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "metrics" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-semibold text-gray-500 uppercase">Comment Ratio</span>
                <p className="text-2xl font-bold text-gray-900 mt-1">{document.metrics.comment_ratio}%</p>
                <span className="text-xs text-gray-400">{document.metrics.comment_lines} comment lines</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-semibold text-gray-500 uppercase">Avg Function Length</span>
                <p className="text-2xl font-bold text-gray-900 mt-1">{document.metrics.avg_function_length} lines</p>
                <span className="text-xs text-gray-400">Max: {document.metrics.max_function_length} lines</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-semibold text-gray-500 uppercase">Nesting Depth</span>
                <p className="text-2xl font-bold text-gray-900 mt-1">{document.metrics.nesting_depth}</p>
                <span className="text-xs text-gray-400">Maximum block depth</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default CodeIntelligenceView;
