import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  FileBox,
  FileCode,
  Files,
  FileSpreadsheet,
  FileText,
  HardDrive,
  Image as ImageIcon,
  Layers,
  Music,
  Package,
  RefreshCw,
  Video,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/services/api";

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState<"all" | "30d" | "7d" | "24h">("all");

  const {
    data: analytics,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["dashboardAnalytics"],
    queryFn: api.getDashboardAnalytics,
    refetchInterval: 15000,
  });

  const { data: conversionsData } = useQuery({
    queryKey: ["dashboardConversionHistory"],
    queryFn: () => api.getConversionHistory({ limit: 5 }),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return <LoadingState message="Loading DocuMind platform metrics..." />;
  }

  if (error || !analytics) {
    return (
      <ErrorState
        title="Failed to Load Dashboard Telemetry"
        message={error instanceof Error ? error.message : "Unable to reach system analytics API."}
        onRetry={() => refetch()}
      />
    );
  }

  const {
    files_summary,
    batches_summary,
    format_distribution,
    recent_files,
    capacity,
    queue_status,
    disk_storage,
  } = analytics;

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getFormatIcon = (cat?: string | null) => {
    switch (cat) {
      case "pdf":
      case "document":
        return <FileText className="h-4 w-4 text-blue-500" />;
      case "spreadsheet":
        return <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
      case "image":
        return <ImageIcon className="h-4 w-4 text-purple-500" />;
      case "audio":
        return <Music className="h-4 w-4 text-pink-500" />;
      case "video":
        return <Video className="h-4 w-4 text-red-500" />;
      case "archive":
        return <Package className="h-4 w-4 text-amber-500" />;
      case "code":
      case "structured_data":
        return <FileCode className="h-4 w-4 text-indigo-500" />;
      default:
        return <FileBox className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const totalFiles = files_summary.total_files;
  const processedPercent =
    totalFiles > 0 ? Math.round((files_summary.processed_files / totalFiles) * 100) : 0;

  return (
    <PageContainer
      title="Platform Overview"
      subtitle="Universal File Intelligence & Bulk Scalability Infrastructure"
      action={
        <div className="flex items-center gap-2">
          {/* Time range selector */}
          <div className="hidden sm:flex items-center rounded-xl bg-muted/60 p-1 border border-border">
            {(["all", "30d", "7d", "24h"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${
                  timeRange === r
                    ? "bg-card text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {r === "all" ? "All Time" : r.toUpperCase()}
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            isLoading={isFetching}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate("/convert")}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Convert Files
          </Button>
        </div>
      }
    >
      {/* Platform Banner */}
      <div className="rounded-2xl border border-blue-500/20 bg-linear-to-r from-blue-500/10 via-indigo-500/5 to-transparent p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-2xs">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-blue-600 text-white shadow-xs">
            <RefreshCw className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-foreground tracking-tight">
                DocuMind Universal File Converter &amp; Extractor
              </h2>
              <Badge variant="primary" size="sm">
                v2.0
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 max-w-xl">
              Upload any supported file → Automatically detect → Extract actual content → Convert to TXT, Markdown, JSON, CSV, HTML, or Mode C ZIP bundles.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-end md:self-center">
          <Button size="sm" onClick={() => navigate("/convert")}>
            Convert a File Now
          </Button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <StatCard
          title="Total Files Processed"
          value={totalFiles.toLocaleString()}
          subtext={`${files_summary.processed_files} completed, ${files_summary.failed_files} errors`}
          icon={<Files className="h-5 w-5 text-blue-500" />}
        />
        <StatCard
          title="Conversion Jobs"
          value={(conversionsData?.meta?.total || conversionsData?.items?.length || 0).toString()}
          subtext="Universal conversions executed"
          icon={<RefreshCw className="h-5 w-5 text-indigo-500" />}
        />
        <StatCard
          title="Storage Consumption"
          value={formatBytes(files_summary.total_storage_bytes)}
          subtext={`${disk_storage.used_gb} GB used (${disk_storage.percent_used}%), ${disk_storage.free_gb} GB free`}
          icon={<HardDrive className="h-5 w-5 text-emerald-500" />}
        />
        <StatCard
          title="Worker Infrastructure"
          value={`${capacity.active_cpu_workers}/${capacity.max_parallel_cpu_workers} Slots`}
          subtext={`${queue_status.total_queued} tasks queued, ${batches_summary.active_batches} active batches`}
          icon={<Cpu className="h-5 w-5 text-purple-500" />}
        />
      </div>

      {/* Distribution & Telemetry Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Format Category Distribution */}
        <div className="rounded-2xl border border-border bg-card p-5 flex flex-col justify-between shadow-2xs">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-500" />
                Format Distribution
              </h3>
              <span className="text-[11px] font-mono text-muted-foreground">
                {Object.keys(format_distribution).length} types
              </span>
            </div>

            {Object.keys(format_distribution).length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                No files categorized yet.
              </div>
            ) : (
              <div className="space-y-3">
                {Object.entries(format_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 6)
                  .map(([cat, count]) => {
                    const pct = totalFiles > 0 ? Math.round((count / totalFiles) * 100) : 0;
                    return (
                      <div key={cat} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="capitalize text-foreground font-medium flex items-center gap-1.5">
                            {getFormatIcon(cat)}
                            {cat}
                          </span>
                          <span className="text-muted-foreground font-mono">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>

          <button
            onClick={() => navigate("/files")}
            className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-primary font-medium hover:underline"
          >
            <span>Explore full format catalog</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Processing Status Breakdown */}
        <div className="rounded-2xl border border-border bg-card p-5 flex flex-col justify-between shadow-2xs">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-500" />
                File Processing State
              </h3>
              <span className="text-[11px] font-mono text-muted-foreground">
                {processedPercent}% completed
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-900 dark:text-emerald-200">
                    Ready &amp; Processed
                  </span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-700 dark:text-emerald-300">
                  {files_summary.processed_files}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
                  <span className="text-xs font-semibold text-blue-900 dark:text-blue-200">
                    In Progress / Detecting
                  </span>
                </div>
                <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">
                  {files_summary.processing_files}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted border border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-foreground">Pending / Queued</span>
                </div>
                <span className="text-xs font-mono font-bold text-muted-foreground">
                  {files_summary.pending_files}
                </span>
              </div>

              {files_summary.failed_files > 0 && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="text-xs font-semibold text-red-900 dark:text-red-200">
                      Failed Files
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-red-600 dark:text-red-400">
                    {files_summary.failed_files}
                  </span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => navigate("/jobs")}
            className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-primary font-medium hover:underline"
          >
            <span>View job logs &amp; retry failed</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Queue Backlog & Worker Health */}
        <div className="rounded-2xl border border-border bg-card p-5 flex flex-col justify-between shadow-2xs">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-500" />
                Queue &amp; Worker Health
              </h3>
              <Badge variant="outline" size="sm">
                4 Priority Tiers
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-muted/60 border border-border/80">
                <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                  Interactive (80+)
                </span>
                <span className="text-sm font-mono font-bold text-foreground">
                  {queue_status.interactive_depth}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-muted/60 border border-border/80">
                <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                  Normal (50..79)
                </span>
                <span className="text-sm font-mono font-bold text-foreground">
                  {queue_status.normal_depth}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-muted/60 border border-border/80">
                <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                  Bulk (20..49)
                </span>
                <span className="text-sm font-mono font-bold text-foreground">
                  {queue_status.bulk_depth}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-muted/60 border border-border/80">
                <span className="text-[10px] text-muted-foreground uppercase font-semibold block">
                  Dead Letter (DLQ)
                </span>
                <span className="text-sm font-mono font-bold text-red-500">
                  {queue_status.dead_letter_depth}
                </span>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-xl bg-card border border-border/80 space-y-1.5 text-xs">
              <div className="flex justify-between text-muted-foreground text-[11px]">
                <span>Active CPU Slots:</span>
                <span className="font-mono text-foreground font-semibold">
                  {capacity.active_cpu_workers} / {capacity.max_parallel_cpu_workers}
                </span>
              </div>
              <div className="flex justify-between text-muted-foreground text-[11px]">
                <span>GPU Mutex Slot:</span>
                <span className="font-mono text-foreground font-semibold">
                  {capacity.active_gpu_workers} / {capacity.max_concurrent_gpu_slots}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate("/bulk-processing")}
            className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-primary font-medium hover:underline"
          >
            <span>Monitor bulk processing</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Recent Files & Batches */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Recent Files Card */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Files className="h-4 w-4 text-blue-500" />
              Recent Files
            </h3>
            <button
              onClick={() => navigate("/files")}
              className="text-xs text-primary font-medium hover:underline"
            >
              View All
            </button>
          </div>

          {recent_files.length === 0 ? (
            <EmptyState
              icon={<Files className="h-6 w-6" />}
              title="No Files Uploaded Yet"
              description="Upload documents, media, or archives to begin intelligence processing."
            />
          ) : (
            <div className="divide-y divide-border/60">
              {recent_files.map((file) => (
                <div
                  key={file.id}
                  onClick={() => navigate("/files")}
                  className="py-2.5 flex items-center justify-between gap-3 hover:bg-muted/40 px-2 rounded-xl transition cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-muted text-muted-foreground shrink-0">
                      {getFormatIcon(file.format_category)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground truncate max-w-xs">
                        {file.filename}
                      </p>
                      <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                        <span className="uppercase font-mono">{file.format_category || "file"}</span>
                        <span>•</span>
                        <span>{formatBytes(file.file_size_bytes)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                        file.status === "ready" || file.status === "processed"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : file.status === "processing"
                            ? "bg-blue-500/10 text-blue-500"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {file.status}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversions Card */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-blue-500" />
              Recent Conversions
            </h3>
            <button
              onClick={() => navigate("/history")}
              className="text-xs text-primary font-medium hover:underline"
            >
              View History
            </button>
          </div>

          {!conversionsData || conversionsData.items.length === 0 ? (
            <EmptyState
              icon={<RefreshCw className="h-6 w-6" />}
              title="No Conversions Yet"
              description="Convert documents, spreadsheets, presentations, code, or media to TXT, MD, JSON, CSV, or HTML."
            />
          ) : (
            <div className="divide-y divide-border/60">
              {conversionsData.items.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => navigate("/history")}
                  className="py-2.5 flex items-center justify-between gap-3 hover:bg-muted/40 px-2 rounded-xl transition cursor-pointer"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-semibold text-foreground truncate max-w-xs">
                        {conv.original_filename}
                      </p>
                      <Badge variant="primary" size="sm" className="uppercase font-mono text-[9px]">
                        .{conv.target_format}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                      <span>{conv.extraction_mode}</span>
                      <span>•</span>
                      <span>{conv.duration_seconds}s</span>
                      <span>•</span>
                      <span>{(conv.output_size_bytes / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                        conv.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : conv.status === "processing"
                          ? "bg-blue-500/10 text-blue-500"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {conv.status}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
};
