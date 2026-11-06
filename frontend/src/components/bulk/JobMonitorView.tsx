import React, { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import { ProcessingJob, JobAttempt, QueueStatus } from "../../types/api";

export const JobMonitorView: React.FC = () => {
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [stageFilter, setStageFilter] = useState<string>("all");
  const [selectedJobAttempts, setSelectedJobAttempts] = useState<{
    jobId: string;
    attempts: JobAttempt[];
  } | null>(null);
  const [attemptsLoading, setAttemptsLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const qStatus = await api.getQueueStatus();
      setQueueStatus(qStatus);

      const status = statusFilter === "all" ? undefined : statusFilter;
      const stage = stageFilter === "all" ? undefined : stageFilter;
      const jobsList = await api.listJobs({ limit: 100, status, stage });
      setJobs(jobsList);
    } catch (err) {
      console.error("Failed to load jobs:", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, stageFilter]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleCancel = async (jobId: string) => {
    setActionLoading(`cancel-${jobId}`);
    try {
      await api.cancelJob(jobId);
      await fetchData();
    } catch (err) {
      console.error("Failed to cancel job:", err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async (jobId: string) => {
    setActionLoading(`retry-${jobId}`);
    try {
      await api.retryJob(jobId);
      await fetchData();
    } catch (err) {
      console.error("Failed to retry job:", err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewAttempts = async (jobId: string) => {
    setAttemptsLoading(true);
    try {
      const attempts = await api.getJobAttempts(jobId);
      setSelectedJobAttempts({ jobId, attempts });
    } catch (err) {
      console.error("Failed to load attempts:", err);
    } finally {
      setAttemptsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-500/20 text-emerald-400">Completed</span>;
      case "processing":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-blue-500/20 text-blue-400 animate-pulse">Running</span>;
      case "queued":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-indigo-500/20 text-indigo-400">Queued</span>;
      case "failed":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-rose-500/20 text-rose-400">Failed</span>;
      case "dead_letter":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-purple-500/20 text-purple-400">Dead Letter</span>;
      case "cancelled":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-500/20 text-slate-400">Cancelled</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-700 text-slate-300">{status}</span>;
    }
  };

  const getStageBadge = (stage: string) => {
    const colors: Record<string, string> = {
      registration: "text-slate-400 border-slate-700",
      detection: "text-amber-400 border-amber-500/30",
      extraction: "text-blue-400 border-blue-500/30",
      ai_indexing: "text-indigo-400 border-indigo-500/30",
      completed: "text-emerald-400 border-emerald-500/30",
    };
    return (
      <span className={`px-2 py-0.5 text-[10px] font-mono border rounded ${colors[stage] || "text-slate-300 border-slate-700"}`}>
        {stage}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Real-time Queue Depth Banner */}
      {queueStatus && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold text-slate-200">Priority Queue Depths & Backlog</span>
            <span className="text-[11px] text-slate-400">
              Active Workers: <span className="text-indigo-400 font-semibold">{queueStatus.active_workers_count}</span>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="bg-slate-800/60 p-2.5 rounded-lg border-l-2 border-indigo-500">
              <span className="block text-[10px] text-slate-400">Interactive (80+)</span>
              <span className="text-base font-bold text-slate-200">{queueStatus.queues.interactive || 0}</span>
            </div>
            <div className="bg-slate-800/60 p-2.5 rounded-lg border-l-2 border-blue-500">
              <span className="block text-[10px] text-slate-400">Normal (50)</span>
              <span className="text-base font-bold text-slate-200">{queueStatus.queues.normal || 0}</span>
            </div>
            <div className="bg-slate-800/60 p-2.5 rounded-lg border-l-2 border-teal-500">
              <span className="block text-[10px] text-slate-400">Bulk (30)</span>
              <span className="text-base font-bold text-slate-200">{queueStatus.queues.bulk || 0}</span>
            </div>
            <div className="bg-slate-800/60 p-2.5 rounded-lg border-l-2 border-slate-500">
              <span className="block text-[10px] text-slate-400">Maintenance (10)</span>
              <span className="text-base font-bold text-slate-200">{queueStatus.queues.maintenance || 0}</span>
            </div>
            <div className="bg-slate-800/60 p-2.5 rounded-lg border-l-2 border-purple-500">
              <span className="block text-[10px] text-purple-400">Dead Letter (DLQ)</span>
              <span className="text-base font-bold text-purple-400">{queueStatus.total_dead_letter || 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Control Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <h2 className="text-base font-semibold text-slate-100">Active Pipeline Jobs</h2>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5">
            <span className="text-xs text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All</option>
              <option value="queued">Queued</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="dead_letter">Dead Letter</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-xs text-slate-400">Stage:</span>
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All</option>
              <option value="registration">Registration</option>
              <option value="detection">Detection</option>
              <option value="extraction">Extraction</option>
              <option value="ai_indexing">AI Indexing</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-sm text-slate-400">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-400">No jobs matching current filter criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Stage</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Progress</th>
                  <th className="py-3 px-4">Worker</th>
                  <th className="py-3 px-4">Retries</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-200 max-w-xs truncate">
                      {job.filename || job.file_id.substring(0, 12)}
                    </td>
                    <td className="py-3 px-4">{getStageBadge(job.stage)}</td>
                    <td className="py-3 px-4">{getStatusBadge(job.status)}</td>
                    <td className="py-3 px-4">
                      <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full"
                          style={{ width: `${Math.min(100, Math.max(0, job.progress))}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {job.current_worker_id ? job.current_worker_id.substring(0, 14) : "—"}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {job.retry_count}/{job.max_retries}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleViewAttempts(job.id)}
                        className="text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        Attempts
                      </button>
                      {["queued", "processing"].includes(job.status) && (
                        <button
                          onClick={() => handleCancel(job.id)}
                          disabled={actionLoading === `cancel-${job.id}`}
                          className="text-rose-400 hover:text-rose-300 transition-colors"
                        >
                          Cancel
                        </button>
                      )}
                      {["failed", "dead_letter"].includes(job.status) && (
                        <button
                          onClick={() => handleRetry(job.id)}
                          disabled={actionLoading === `retry-${job.id}`}
                          className="text-amber-400 hover:text-amber-300 transition-colors"
                        >
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Attempts Modal */}
      {selectedJobAttempts && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-100">Job Attempts Audit</h3>
              <button
                onClick={() => setSelectedJobAttempts(null)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                &times;
              </button>
            </div>

            {attemptsLoading ? (
              <div className="p-4 text-center text-xs text-slate-400">Loading attempts...</div>
            ) : selectedJobAttempts.attempts.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No attempts logged yet for this job.</div>
            ) : (
              <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                {selectedJobAttempts.attempts.map((att) => (
                  <div key={att.id} className="p-3 bg-slate-800/60 rounded-lg text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-slate-200">Attempt #{att.attempt_number}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-700 text-slate-300 font-mono">
                        {att.status}
                      </span>
                    </div>
                    <div className="text-slate-400 text-[11px] font-mono">
                      <span>Worker: {att.worker_id}</span>
                      {att.duration_ms && <span className="ml-3">Duration: {att.duration_ms.toFixed(1)}ms</span>}
                      {att.memory_peak_mb && <span className="ml-3">Peak: {att.memory_peak_mb.toFixed(1)}MB</span>}
                    </div>
                    {att.error_message && (
                      <p className="text-rose-400 text-[11px] pt-1 font-mono">{att.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedJobAttempts(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
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
