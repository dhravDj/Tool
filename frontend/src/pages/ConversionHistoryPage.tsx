import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  History,
  Download,
  Trash2,
  RefreshCw,
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Filter,
} from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { ConversionRecordDTO } from "@/types/api";

export const ConversionHistoryPage: React.FC = () => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [page, setPage] = useState<number>(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedRecord, setSelectedRecord] = useState<ConversionRecordDTO | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["conversionHistory", page, statusFilter],
    queryFn: () =>
      api.getConversionHistory({
        page,
        limit: 15,
        status: statusFilter || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteConversion(id),
    onSuccess: () => {
      showToast({ type: "success", title: "Deleted", message: "Conversion record deleted." });
      queryClient.invalidateQueries({ queryKey: ["conversionHistory"] });
      if (selectedRecord) setSelectedRecord(null);
    },
    onError: (err: unknown) => {
      const errMsg = err instanceof Error ? err.message : "Failed to delete record.";
      showToast({ type: "error", title: "Error", message: errMsg });
    },
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => api.retryConversion(id),
    onSuccess: () => {
      showToast({ type: "success", title: "Queued", message: "Conversion queued for retry." });
      queryClient.invalidateQueries({ queryKey: ["conversionHistory"] });
    },
    onError: (err: unknown) => {
      const errMsg = err instanceof Error ? err.message : "Failed to retry conversion.";
      showToast({ type: "error", title: "Error", message: errMsg });
    },
  });

  const items = data?.items || [];
  const meta = data?.meta;

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-400">
            <RefreshCw className="w-3 h-3 animate-spin" /> Processing
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-400">
            <XCircle className="w-3 h-3" /> Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
            <Clock className="w-3 h-3" /> {status}
          </span>
        );
    }
  };

  return (
    <PageContainer
      title="Conversion History"
      subtitle="Review past conversion jobs, inspect extracted preview outputs, and download converted files."
    >
      <div className="space-y-6">
        {/* Controls bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <div className="flex items-center gap-3">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Filter by Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>

        {/* History Table */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="py-12">
              <LoadingState message="Loading conversion history..." />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-16">
              <History className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">No conversions recorded yet</p>
              <p className="text-xs text-slate-500 mt-1">Convert your first file to see history entries here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 uppercase font-semibold">
                  <tr>
                    <th className="py-3 px-4">Source File</th>
                    <th className="py-3 px-4">Conversion</th>
                    <th className="py-3 px-4">Mode</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Duration & Size</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {items.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100 max-w-[220px] truncate">
                        {row.original_filename}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono uppercase font-bold text-slate-600 dark:text-slate-400">
                            {row.source_format}
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-400" />
                          <Badge variant="primary" className="uppercase font-mono text-[10px]">
                            {row.target_format}
                          </Badge>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-500 capitalize">{row.extraction_mode.replace("_", " ")}</td>
                      <td className="py-3 px-4">{renderStatusBadge(row.status)}</td>
                      <td className="py-3 px-4 text-slate-500">
                        {row.duration_seconds}s • {(row.output_size_bytes / 1024).toFixed(1)} KB
                      </td>
                      <td className="py-3 px-4 text-slate-500">
                        {row.created_at ? new Date(row.created_at).toLocaleString() : "-"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {row.status === "completed" && (
                            <>
                              <button
                                title="Preview extracted text"
                                onClick={() => setSelectedRecord(row)}
                                className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <a
                                title="Download converted artifact"
                                href={api.getConversionDownloadUrl(row.id)}
                                download={row.output_filename}
                                className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
                              >
                                <Download className="w-4 h-4" />
                              </a>
                            </>
                          )}
                          {row.status === "failed" && (
                            <button
                              title="Retry conversion"
                              onClick={() => retryMutation.mutate(row.id)}
                              className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            title="Delete conversion"
                            onClick={() => {
                              if (window.confirm(`Delete record for ${row.output_filename}?`)) {
                                deleteMutation.mutate(row.id);
                              }
                            }}
                            className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {meta && meta.total_pages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500">
              <span>
                Page {meta.page} of {meta.total_pages} ({meta.total} conversions)
              </span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= meta.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Preview Modal */}
        {selectedRecord && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                    {selectedRecord.output_filename}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
                >
                  ✕
                </button>
              </div>

              <div className="p-4 overflow-auto flex-1 font-mono text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap bg-slate-50 dark:bg-slate-950">
                {selectedRecord.preview_content || "No preview text available."}
              </div>

              <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Size: {(selectedRecord.output_size_bytes / 1024).toFixed(1)} KB • Duration:{" "}
                  {selectedRecord.duration_seconds}s
                </span>
                <a
                  href={api.getConversionDownloadUrl(selectedRecord.id)}
                  download={selectedRecord.output_filename}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download File
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
