import React, { useState, useEffect } from "react";
import { api } from "../../services/api";
import { SystemCapacity, WorkerStatus, ResourceUsage } from "../../types/api";

export const ProcessingAnalyticsView: React.FC = () => {
  const [capacity, setCapacity] = useState<SystemCapacity | null>(null);
  const [workers, setWorkers] = useState<WorkerStatus[]>([]);
  const [resources, setResources] = useState<ResourceUsage | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchMetrics = async () => {
    try {
      const [cap, wks, res] = await Promise.all([
        api.getSystemCapacity(),
        api.getWorkerStatus(),
        api.getResourceUsage(),
      ]);
      setCapacity(cap);
      setWorkers(wks);
      setResources(res);
    } catch (err) {
      console.error("Failed to load telemetry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* System Capacity & Backpressure Overview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">System Processing Capacity</h2>
            <p className="text-xs text-slate-400">
              Hardware-governed throughput bounds, slot limits, and dynamic backpressure status.
            </p>
          </div>

          {capacity && (
            <div
              className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center space-x-2 ${
                capacity.is_under_backpressure
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  capacity.is_under_backpressure ? "bg-amber-400 animate-ping" : "bg-emerald-400"
                }`}
              />
              <span>
                {capacity.is_under_backpressure
                  ? `Backpressure Active: ${capacity.backpressure_reason || "Queue backlog"}`
                  : "System Healthy — Unthrottled"}
              </span>
            </div>
          )}
        </div>

        {loading || !capacity ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading capacity metrics...</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-800">
              <span className="block text-xs text-slate-400">Parallel CPU Workers</span>
              <span className="text-2xl font-bold text-indigo-400">
                {capacity.max_parallel_cpu_workers} slots
              </span>
              <span className="block text-[11px] text-slate-500 mt-1">Bounded concurrency</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-800">
              <span className="block text-xs text-slate-400">GPU Inference Slots</span>
              <span className="text-2xl font-bold text-teal-400">
                {capacity.max_concurrent_gpu_slots} slot
              </span>
              <span className="block text-[11px] text-slate-500 mt-1">Single-slot VRAM isolation</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-800">
              <span className="block text-xs text-slate-400">Extraction Throughput</span>
              <span className="text-2xl font-bold text-blue-400">
                ~{capacity.extraction_capacity_files_per_sec.toFixed(0)} files/s
              </span>
              <span className="block text-[11px] text-slate-500 mt-1">Phases 3–10 routing</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-800">
              <span className="block text-xs text-slate-400">AI Indexing Capacity</span>
              <span className="text-2xl font-bold text-purple-400">
                ~{capacity.ai_indexing_capacity_chunks_per_sec.toFixed(0)} chunks/s
              </span>
              <span className="block text-[11px] text-slate-500 mt-1">Embedding pipeline</span>
            </div>
          </div>
        )}
      </div>

      {/* Host Hardware Metrics */}
      {resources && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-semibold text-slate-100 mb-4">Host Hardware Telemetry</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CPU */}
            <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 border border-slate-800">
              <span className="text-xs font-semibold text-slate-300">CPU Compute</span>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Logical Cores:</span>
                <span className="font-semibold text-slate-200">{resources.cpu.logical_cores}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Recommended Limit:</span>
                <span className="font-semibold text-slate-200">{resources.cpu.recommended_workers} workers</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Active Slots Limit:</span>
                <span className="font-semibold text-indigo-400">{resources.cpu.active_workers_limit}</span>
              </div>
            </div>

            {/* RAM */}
            <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 border border-slate-800">
              <span className="text-xs font-semibold text-slate-300">Host Memory</span>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Total RAM:</span>
                <span className="font-semibold text-slate-200">
                  {(resources.memory.total_ram_mb / 1024).toFixed(1)} GB
                </span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Available Free:</span>
                <span className="font-semibold text-emerald-400">
                  {(resources.memory.free_ram_mb / 1024).toFixed(1)} GB
                </span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-1.5 overflow-hidden mt-2">
                <div
                  className="bg-indigo-500 h-full"
                  style={{
                    width: `${Math.round(
                      ((resources.memory.total_ram_mb - resources.memory.free_ram_mb) /
                        resources.memory.total_ram_mb) *
                        100
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* Storage */}
            <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 border border-slate-800">
              <span className="text-xs font-semibold text-slate-300">Local Storage</span>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Disk Size:</span>
                <span className="font-semibold text-slate-200">{resources.storage.total_gb} GB</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>Free Disk:</span>
                <span className="font-semibold text-emerald-400">{resources.storage.free_gb} GB</span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-1.5 overflow-hidden mt-2">
                <div
                  className="bg-teal-500 h-full"
                  style={{ width: `${resources.storage.percent_used}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Worker Fleet Telemetry */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-100 mb-4">Autonomous Worker Fleet</h3>

        {workers.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            No active worker heartbeats registered. Scalable worker processes send heartbeats every 10 seconds.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Worker ID</th>
                  <th className="py-2.5 px-3">Hostname (PID)</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">CPU %</th>
                  <th className="py-2.5 px-3">RAM (MB)</th>
                  <th className="py-2.5 px-3">Completed</th>
                  <th className="py-2.5 px-3">Failed</th>
                  <th className="py-2.5 px-3">Last Heartbeat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {workers.map((w) => (
                  <tr key={w.worker_id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-200">
                      {w.worker_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {w.hostname} ({w.pid})
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          w.status === "alive"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-slate-700 text-slate-300"
                        }`}
                      >
                        {w.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{w.cpu_percent.toFixed(1)}%</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{w.memory_mb.toFixed(0)} MB</td>
                    <td className="py-2.5 px-3 font-mono text-emerald-400">{w.jobs_completed}</td>
                    <td className="py-2.5 px-3 font-mono text-rose-400">{w.jobs_failed}</td>
                    <td className="py-2.5 px-3 text-[11px] text-slate-400">
                      {new Date(w.last_heartbeat).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
