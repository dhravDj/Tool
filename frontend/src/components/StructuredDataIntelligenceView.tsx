import React, { useState, useEffect } from "react";
import {
  StructuredDataDocument,
  StructuredDataAnalysisOverview,
  ColumnProfile,
} from "../types/api";
import { api } from "../services/api";

interface StructuredDataIntelligenceViewProps {
  fileId: string;
  filename: string;
  onClose?: () => void;
}

export const StructuredDataIntelligenceView: React.FC<StructuredDataIntelligenceViewProps> = ({
  fileId,
  filename,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<
    "overview" | "columns" | "records" | "schema"
  >("overview");
  const [document, setDocument] = useState<StructuredDataDocument | null>(null);
  const [overview, setOverview] = useState<StructuredDataAnalysisOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchKey, setSearchKey] = useState<string>("");

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [docRes, ovRes] = await Promise.all([
          api.getStructuredDataDocumentResult(fileId),
          api.getStructuredDataAnalysis(fileId).catch(() => null),
        ]);
        if (isMounted) {
          setDocument(docRes);
          setOverview(ovRes);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load structured data intelligence");
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
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent" />
          <p className="text-sm font-medium text-gray-600">Profiling structured data & schema...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="p-6 bg-red-50 text-red-700 rounded-lg">
        <p className="font-semibold">Error Loading Structured Data</p>
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

  const filteredColumns = document.data_profile.column_profiles.filter((c: ColumnProfile) =>
    c.name.toLowerCase().includes(searchKey.toLowerCase()) ||
    c.data_type.toLowerCase().includes(searchKey.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          <span className="px-2.5 py-1 text-xs font-bold uppercase rounded bg-emerald-100 text-emerald-800">
            {document.format}
          </span>
          <div>
            <h2 className="text-lg font-bold text-gray-900">{filename}</h2>
            <p className="text-xs text-gray-500">
              Root: {document.root_type} • {document.data_profile.total_rows} rows • {document.data_profile.total_columns} columns
              {overview?.compression ? ` • Compression: ${overview.compression}` : ""}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={api.getStructuredDataExportUrl(fileId, "json")}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Export JSON
          </a>
          <a
            href={api.getStructuredDataExportUrl(fileId, "markdown")}
            target="_blank"
            rel="noreferrer"
            className="ml-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Export Markdown
          </a>
          <a
            href={api.getStructuredDataExportUrl(fileId, "csv")}
            target="_blank"
            rel="noreferrer"
            className="ml-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Export CSV
          </a>
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
          { id: "overview", label: "Overview & Security" },
          { id: "columns", label: `Column Profiles (${document.data_profile.column_profiles.length})` },
          { id: "records", label: `Sample Records (${document.records.length})` },
          { id: "schema", label: "Schema Definition" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id
                ? "border-emerald-600 text-emerald-600"
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
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Rows / Records</span>
                <p className="text-2xl font-bold text-gray-900 mt-1">{document.data_profile.total_rows}</p>
                <span className="text-xs text-gray-400">Total counted</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Columns / Fields</span>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{document.data_profile.total_columns}</p>
                <span className="text-xs text-gray-400">Distinct schema fields</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Candidate Keys</span>
                <p className="text-2xl font-bold text-indigo-600 mt-1">
                  {document.data_profile.candidate_keys.length}
                </p>
                <span className="text-xs text-gray-400">Unique identifier fields</span>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Validation</span>
                <p className={`text-2xl font-bold mt-1 ${document.validation_results.is_valid ? "text-emerald-600" : "text-red-600"}`}>
                  {document.validation_results.is_valid ? "Valid" : "Invalid"}
                </p>
                <span className="text-xs text-gray-400">
                  {document.validation_results.duplicate_keys.length} duplicate keys
                </span>
              </div>
            </div>

            {/* Security Alerts */}
            {document.validation_results.security_warnings.length > 0 && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <h3 className="text-sm font-semibold text-amber-800">Security Warning Detected</h3>
                <ul className="mt-2 list-disc list-inside text-xs text-amber-700 space-y-1">
                  {document.validation_results.security_warnings.map((warn, i) => (
                    <li key={i}>{warn}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Duplicate Keys Warning */}
            {document.validation_results.duplicate_keys.length > 0 && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <h3 className="text-sm font-semibold text-amber-800">Duplicate Keys Warning</h3>
                <p className="text-xs text-amber-700 mt-1">
                  The following keys appear multiple times in the mapping: {document.validation_results.duplicate_keys.join(", ")}
                </p>
              </div>
            )}

            {/* Raw preview */}
            {document.raw_preview && (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <h4 className="text-xs font-semibold text-gray-700 uppercase">Document Preview</h4>
                </div>
                <pre className="p-4 font-mono text-xs bg-gray-900 text-gray-100 overflow-x-auto max-h-64">
                  {document.raw_preview}
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === "columns" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <input
                type="text"
                value={searchKey}
                onChange={(e) => setSearchKey(e.target.value)}
                placeholder="Search columns or data types..."
                className="w-72 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-emerald-500"
              />
              <span className="text-xs text-gray-500">
                {filteredColumns.length} of {document.data_profile.column_profiles.length} columns
              </span>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Column Name</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Null %</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Unique / Key</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {filteredColumns.map((col) => (
                    <tr key={col.name} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono font-medium text-gray-900">{col.name}</td>
                      <td className="px-4 py-2">
                        <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-800 font-mono">
                          {col.data_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-xs">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-red-500 h-1.5 rounded-full"
                              style={{ width: `${col.null_percentage}%` }}
                            />
                          </div>
                          <span className="text-gray-500">{col.null_percentage}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-2 text-xs">
                        {col.is_candidate_key ? (
                          <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-medium">
                            Candidate Key
                          </span>
                        ) : col.is_unique ? (
                          <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                            Unique
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-xs font-mono text-gray-600">
                        {col.statistics?.sample_values?.slice(0, 3).map(String).join(", ") || "—"}
                      </td>
                    </tr>
                  ))}
                  {filteredColumns.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                        No columns match search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "records" && (
          <div className="space-y-4">
            <div className="border border-gray-200 rounded-lg overflow-x-auto">
              {document.records.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(document.records[0]).map((k) => (
                        <th key={k} className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
                          {k}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {document.records.map((r, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {Object.keys(document.records[0]).map((k) => (
                          <td key={k} className="px-4 py-2 font-mono text-xs text-gray-700 whitespace-nowrap">
                            {r[k] === null || r[k] === undefined ? "—" : String(r[k])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  No sample records available for this structured file.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "schema" && (
          <div className="space-y-4">
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
                <span className="text-xs font-semibold text-gray-700 uppercase">Schema Definition</span>
              </div>
              <pre className="p-4 font-mono text-xs bg-gray-900 text-gray-100 overflow-x-auto max-h-[500px]">
                {JSON.stringify(document.schema_definition, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default StructuredDataIntelligenceView;
