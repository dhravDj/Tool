import React, { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import { ProcessingBatch, BatchFileItem, BatchReport } from "../../types/api";

interface BatchProcessingViewProps {
  onSelectBatch?: (batchId: string) => void;
}

export const BatchProcessingView: React.FC<BatchProcessingViewProps> = () => {
  const [batches, setBatches] = useState<ProcessingBatch[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [batchFiles, setBatchFiles] = useState<BatchFileItem[]>([]);
  const [filesLoading, setFilesLoading] = useState<boolean>(false);
  const [reportModal, setReportModal] = useState<BatchReport | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchBatches = useCallback(async () => {
    try {
      const filter = statusFilter === "all" ? undefined : statusFilter;
      const data = await api.listBatches({ limit: 100, status: filter });
      setBatches(data);
    } catch (err) {
      console.error("Failed to load batches:", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchBatches();
    const interval = setInterval(fetchBatches, 4000);
    return () => clearInterval(interval);
  }, [fetchBatches]);

  const loadBatchFiles = async (batchId: string) => {
    setSelectedBatchId(batchId);
    setFilesLoading(true);
    try {
      const files = await api.listBatchFiles(batchId, { limit: 200 });
      setBatchFiles(files);
    } catch (err) {
      console.error("Failed to load batch files:", err);
    } finally {
      setFilesLoading(false);
    }
  };

  const handleAction = async (action: "start" | "pause" | "resume" | "cancel" | "retry", batchId: string) => {
    setActionLoading(`${action}-${batchId}`);
    try {
      if (action === "start") await api.startBatch(batchId);
      if (action === "pause") await api.pauseBatch(batchId);
      if (action === "resume") await api.resumeBatch(batchId);
      if (action === "cancel") await api.cancelBatch(batchId);
      if (action === "retry") await api.retryFailedBatch(batchId);
      await fetchBatches();
    } catch (err) {
      console.error(`Failed to execute ${action} on batch:`, err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExportReport = async (batchId: string) => {
    try {
      const report = await api.getBatchReport(batchId);
      setReportModal(report);
    } catch (err) {
      console.error("Failed to fetch batch report:", err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400">Completed</span>;
      case "processing":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-500/20 text-blue-400 animate-pulse">Processing</span>;
      case "paused":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-400">Paused</span>;
      case "partially_completed":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-teal-500/20 text-teal-400">Partial</span>;
      case "failed":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400">Failed</span>;
      case "cancelled":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-500/20 text-slate-400">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-400">Pending</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Processing Batches</h2>
          <p className="text-xs text-slate-400">Manage high-throughput batch lifecycles, progress, and job routing.</p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Filter:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="partially_completed">Partially Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button
            onClick={() => fetchBatches()}
            className="p-1.5 text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            title="Refresh Batches"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Batches List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Loading batches...</div>
      ) : batches.length === 0 ? (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-sm">
          No processing batches found. Upload files in the Ingestion tab to create a batch.
        </div>
      ) : (
        <div className="space-y-4">
          {batches.map((batch) => (
            <div
              key={batch.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors shadow-sm"
            >
              <div className="flex flex-col lg:flex-row justify-between lg:items-center gap-4 mb-4">
                <div>
                  <div className="flex items-center space-x-3 mb-1">
                    <h3 className="text-base font-semibold text-slate-100">{batch.name}</h3>
                    {getStatusBadge(batch.status)}
                  </div>
                  <div className="flex items-center space-x-4 text-xs text-slate-400 font-mono">
                    <span>ID: {batch.id.substring(0, 18)}...</span>
                    <span>Created: {new Date(batch.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Control Actions */}
                <div className="flex flex-wrap items-center gap-2">
                  {batch.status === "pending" && (
                    <button
                      onClick={() => handleAction("start", batch.id)}
                      disabled={actionLoading === `start-${batch.id}`}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition-colors"
                    >
                      Start Batch
                    </button>
                  )}
                  {batch.status === "processing" && (
                    <button
                      onClick={() => handleAction("pause", batch.id)}
                      disabled={actionLoading === `pause-${batch.id}`}
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded-lg transition-colors"
                    >
                      Pause
                    </button>
                  )}
                  {batch.status === "paused" && (
                    <button
                      onClick={() => handleAction("resume", batch.id)}
                      disabled={actionLoading === `resume-${batch.id}`}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg transition-colors"
                    >
                      Resume
                    </button>
                  )}
                  {["pending", "processing", "paused"].includes(batch.status) && (
                    <button
                      onClick={() => handleAction("cancel", batch.id)}
                      disabled={actionLoading === `cancel-${batch.id}`}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-rose-400 text-xs font-medium rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                  {(batch.failed_files > 0 || batch.status === "failed") && (
                    <button
                      onClick={() => handleAction("retry", batch.id)}
                      disabled={actionLoading === `retry-${batch.id}`}
                      className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium rounded-lg transition-colors"
                    >
                      Retry Failed ({batch.failed_files})
                    </button>
                  )}
                  <button
                    onClick={() => loadBatchFiles(batch.id)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
                  >
                    View Files ({batch.total_files})
                  </button>
                  <button
                    onClick={() => handleExportReport(batch.id)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
                  >
                    Export Report
                  </button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Work-Weighted Progress</span>
                  <span className="font-semibold text-slate-200">{batch.overall_progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      batch.status === "completed"
                        ? "bg-emerald-500"
                        : batch.status === "failed"
                        ? "bg-rose-500"
                        : "bg-indigo-500"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, batch.overall_progress))}%` }}
                  />
                </div>
              </div>

              {/* File Breakdown Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 mt-4 text-center">
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-slate-400">Total</span>
                  <span className="text-xs font-bold text-slate-200">{batch.total_files}</span>
                </div>
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-indigo-400">Queued</span>
                  <span className="text-xs font-bold text-indigo-400">{batch.queued_files}</span>
                </div>
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-blue-400">Processing</span>
                  <span className="text-xs font-bold text-blue-400">{batch.processing_files}</span>
                </div>
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-emerald-400">Completed</span>
                  <span className="text-xs font-bold text-emerald-400">{batch.completed_files}</span>
                </div>
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-rose-400">Failed</span>
                  <span className="text-xs font-bold text-rose-400">{batch.failed_files}</span>
                </div>
                <div className="bg-slate-800/40 p-2 rounded">
                  <span className="block text-[11px] text-slate-400">Cancelled</span>
                  <span className="text-xs font-bold text-slate-400">{batch.cancelled_files}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Files Drawer Modal */}
      {selectedBatchId && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-slate-900 border-l border-slate-800 w-full max-w-xl h-full p-6 overflow-y-auto space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="text-base font-semibold text-slate-100">Batch File Inventory</h3>
              <button
                onClick={() => setSelectedBatchId(null)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                &times;
              </button>
            </div>

            {filesLoading ? (
              <div className="p-8 text-center text-sm text-slate-400">Loading files...</div>
            ) : batchFiles.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-400">No files registered in this batch.</div>
            ) : (
              <div className="space-y-2">
                {batchFiles.map((file) => (
                  <div
                    key={file.id}
                    className="p-3 bg-slate-800/60 rounded-lg text-xs space-y-1 border border-slate-800"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-slate-200 truncate max-w-xs">{file.filename}</span>
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-700 text-slate-300">
                        {file.status}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400 text-[11px]">
                      <span>Size: {(file.file_size / 1024).toFixed(1)} KB</span>
                      <span>Dedup: {file.dedup_decision || "new"}</span>
                    </div>
                    {file.validation_error && (
                      <p className="text-rose-400 text-[11px] pt-1">{file.validation_error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Report Modal */}
      {reportModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="text-base font-semibold text-slate-100">
                Audit Report: {reportModal.name}
              </h3>
              <button
                onClick={() => setReportModal(null)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                &times;
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-300 overflow-x-auto max-h-96">
              <pre>{JSON.stringify(reportModal, null, 2)}</pre>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(reportModal, null, 2)], {
                    type: "application/json",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `report_${reportModal.batch_id}.json`;
                  a.click();
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                Download JSON Report
              </button>
              <button
                onClick={() => setReportModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
