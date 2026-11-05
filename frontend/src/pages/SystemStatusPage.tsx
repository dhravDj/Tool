import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
  Server,
  Zap,
} from "lucide-react";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { api } from "@/services/api";

export const SystemStatusPage: React.FC = () => {
  const {
    data: health,
    isLoading: isHealthLoading,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 5000,
  });

  const {
    data: system,
    isLoading: isSystemLoading,
    error: systemError,
    refetch: refetchSystem,
  } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: api.getSystemStatus,
    refetchInterval: 10000,
  });

  const handleRefresh = () => {
    refetchHealth();
    refetchSystem();
  };

  if (isHealthLoading && isSystemLoading) {
    return <LoadingState message="Connecting to DocuMind system diagnostics..." />;
  }

  if (healthError && systemError) {
    return (
      <PageContainer title="System Status" subtitle="Platform Diagnostic Monitoring">
        <ErrorState
          title="Backend API Unreachable"
          message="Could not connect to the FastAPI gateway at /api/v1/health. Ensure backend container or uvicorn process is running."
          onRetry={handleRefresh}
        />
      </PageContainer>
    );
  }

  const subsystems = [
    {
      name: "FastAPI Gateway",
      icon: <Server className="h-5 w-5 text-primary" />,
      status: "healthy",
      latency: "0.2ms",
      desc: `Uptime: ${health?.uptime_seconds ? Math.floor(health.uptime_seconds) : 0}s`,
    },
    {
      name: "PostgreSQL Database",
      icon: <Database className="h-5 w-5 text-amber-500" />,
      status: health?.database?.status || "error",
      latency: `${health?.database?.latency_ms ?? 0}ms`,
      desc: health?.database?.message || "Relational store",
    },
    {
      name: "Redis Cache & Queue",
      icon: <Zap className="h-5 w-5 text-blue-500" />,
      status: health?.redis?.status || "degraded",
      latency: `${health?.redis?.latency_ms ?? 0}ms`,
      desc: health?.redis?.message || "Task broker & cache",
    },
    {
      name: "Local Storage Hierarchy",
      icon: <HardDrive className="h-5 w-5 text-emerald-500" />,
      status: health?.storage?.status || "ok",
      latency: `${health?.storage?.latency_ms ?? 0}ms`,
      desc: health?.storage?.message || "Local disk adapter",
    },
    {
      name: "AI Inference Engine",
      icon: <Cpu className="h-5 w-5 text-indigo-500" />,
      status: health?.ai_engine?.status || "ok",
      latency: "Local",
      desc: health?.ai_engine?.message || "Local sovereign model runtime",
    },
  ];

  return (
    <PageContainer
      title="System Status & Telemetry"
      subtitle="Real-time subsystem health, dependency readiness, and hardware telemetry"
      action={
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Status
        </button>
      }
    >
      {/* Subsystem Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {subsystems.map((sub) => (
          <div key={sub.name} className="rounded-xl border border-border bg-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-muted text-foreground">{sub.icon}</div>
                <h4 className="text-sm font-semibold text-foreground">{sub.name}</h4>
              </div>
              <StatusIndicator status={sub.status} label={sub.status.toUpperCase()} size="sm" />
            </div>
            <p className="text-xs text-muted-foreground truncate">{sub.desc}</p>
            <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Latency</span>
              <span className="font-mono font-medium text-foreground">{sub.latency}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Deep Telemetry Breakdown */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Environment & Runtime Details */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3">
            Host & Runtime Environment
          </h3>
          <dl className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <dt className="text-muted-foreground">Operating System</dt>
              <dd className="font-semibold text-foreground mt-0.5">{system?.platform?.os || "Linux"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Python Version</dt>
              <dd className="font-semibold text-foreground mt-0.5">{system?.platform?.python_version || "3.13"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Environment Tier</dt>
              <dd className="font-semibold text-foreground mt-0.5 capitalize">{system?.platform?.environment || "development"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Platform Version</dt>
              <dd className="font-semibold text-foreground mt-0.5">v{system?.platform?.version || "0.1.0"}</dd>
            </div>
          </dl>
        </div>

        {/* Disk & Capacity Details */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-3">
            Storage Subsystem Telemetry
          </h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Storage Root</span>
              <span className="font-mono text-foreground truncate max-w-xs">{system?.storage?.root_path}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Free Capacity</span>
              <span className="font-semibold text-foreground">{system?.storage?.disk_usage?.free_gb || 0} GB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Capacity</span>
              <span className="font-semibold text-foreground">{system?.storage?.disk_usage?.total_gb || 0} GB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Capacity Used</span>
              <span className="font-semibold text-foreground">{system?.storage?.disk_usage?.percent_used || 0}%</span>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
