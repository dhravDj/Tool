import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Cpu,
  Database,
  FileCheck2,
  HardDrive,
  Layers,
  Sparkles,
  Zap,
} from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { StatCard } from "@/components/ui/StatCard";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { api } from "@/services/api";

export const DashboardPage: React.FC = () => {
  const { data: health, isLoading: isHealthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 10000,
  });

  const { data: system, isLoading: isSystemLoading } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: api.getSystemStatus,
  });

  const { data: pluginsData } = useQuery({
    queryKey: ["plugins"],
    queryFn: () => api.getPlugins(),
  });

  if (isHealthLoading && isSystemLoading) {
    return <LoadingState message="Loading DocuMind platform dashboard..." />;
  }

  const aiMode = system?.ai_engine?.mode || "local";
  const pluginsCount = pluginsData?.total_plugins ?? 0;
  const storageUsed = system?.storage?.disk_usage?.percent_used ?? 0;

  return (
    <PageContainer
      title="Platform Overview"
      subtitle="Universal File Intelligence Platform — Engineering Foundation"
    >
      {/* Phase 1 Status Banner */}
      <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Phase 1 Foundation Active</h4>
            <p className="text-xs text-muted-foreground">
              Modular Monolith architecture, database schemas, plugin interfaces, and health monitoring are live.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-muted border border-border">
            v{system?.platform?.version || "0.1.0"}
          </span>
          <StatusIndicator status={health?.status || "ok"} label={health?.status?.toUpperCase()} />
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <StatCard
          title="AI Execution Mode"
          value={aiMode.toUpperCase()}
          subtext={`Provider: ${system?.ai_engine?.local_provider || "ollama"} (${system?.ai_engine?.device || "cpu"})`}
          icon={<Cpu className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Registered Plugins"
          value={pluginsCount}
          subtext="Detectors, Extractors, AI & Formatters"
          icon={<Layers className="h-5 w-5 text-blue-500" />}
        />
        <StatCard
          title="Storage Subsystem"
          value={`${storageUsed}%`}
          subtext={`${system?.storage?.disk_usage?.free_gb || 0} GB free capacity`}
          icon={<HardDrive className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Database State"
          value={health?.database?.status === "ok" ? "Connected" : "Standby"}
          subtext={`PostgreSQL (${health?.database?.latency_ms ?? 0} ms)`}
          icon={<Database className="h-5 w-5 text-amber-500" />}
        />
      </div>

      {/* Subsystem & Plugin Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Left Column: Registered Plugins List */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <div>
              <h3 className="text-base font-semibold text-foreground">Registered Core Plugins</h3>
              <p className="text-xs text-muted-foreground">Active adapters complying with Phase 1 interfaces</p>
            </div>
            <span className="text-xs font-mono bg-muted px-2 py-1 rounded text-muted-foreground">
              {pluginsCount} plugins
            </span>
          </div>

          {pluginsData?.plugins && pluginsData.plugins.length > 0 ? (
            <div className="divide-y divide-border/60">
              {pluginsData.plugins.map((plugin) => (
                <div key={plugin.name} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 truncate">
                    <div className="p-2 rounded bg-muted/70 text-foreground shrink-0">
                      <Zap className="h-4 w-4" />
                    </div>
                    <div className="truncate">
                      <p className="text-sm font-medium text-foreground truncate">{plugin.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{plugin.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">
                      {plugin.plugin_type}
                    </span>
                    <StatusIndicator status="ok" label="Active" size="sm" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No Plugins Registered"
              description="Plugins will appear here once loaded by the backend registry."
            />
          )}
        </div>

        {/* Right Column: Processing Activity Shell */}
        <div className="rounded-xl border border-border bg-card p-5 flex flex-col">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <div>
              <h3 className="text-base font-semibold text-foreground">Recent Activity</h3>
              <p className="text-xs text-muted-foreground">Batch execution and job progress</p>
            </div>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>

          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={<FileCheck2 className="h-8 w-8" />}
              title="No Active Batches"
              description="Extraction engines are deferred to Phase 2. Batch ingestion will populate records here."
            />
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
