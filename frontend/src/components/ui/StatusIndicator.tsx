import React from "react";
import { cn } from "@/lib/utils";

type StatusType = "ok" | "healthy" | "completed" | "processing" | "degraded" | "error" | "unhealthy" | "failed" | "pending" | "stored" | "alive";

interface StatusIndicatorProps {
  status: string;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = "md",
  className,
}) => {
  const normalized = status.toLowerCase() as StatusType;

  const colorMap: Record<string, { dot: string; bg: string; text: string }> = {
    ok: { dot: "bg-emerald-500", bg: "bg-emerald-500/10", text: "text-emerald-500" },
    healthy: { dot: "bg-emerald-500", bg: "bg-emerald-500/10", text: "text-emerald-500" },
    alive: { dot: "bg-emerald-500", bg: "bg-emerald-500/10", text: "text-emerald-500" },
    completed: { dot: "bg-emerald-500", bg: "bg-emerald-500/10", text: "text-emerald-500" },
    processing: { dot: "bg-blue-500 animate-pulse", bg: "bg-blue-500/10", text: "text-blue-500" },
    degraded: { dot: "bg-amber-500", bg: "bg-amber-500/10", text: "text-amber-500" },
    stored: { dot: "bg-indigo-500", bg: "bg-indigo-500/10", text: "text-indigo-500" },
    pending: { dot: "bg-slate-400", bg: "bg-slate-400/10", text: "text-slate-400" },
    error: { dot: "bg-rose-500", bg: "bg-rose-500/10", text: "text-rose-500" },
    unhealthy: { dot: "bg-rose-500", bg: "bg-rose-500/10", text: "text-rose-500" },
    failed: { dot: "bg-rose-500", bg: "bg-rose-500/10", text: "text-rose-500" },
  };

  const scheme = colorMap[normalized] || {
    dot: "bg-slate-400",
    bg: "bg-slate-400/10",
    text: "text-slate-400",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-medium border border-border/40",
        size === "sm" ? "text-xs" : "text-xs tracking-wide",
        scheme.bg,
        scheme.text,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", scheme.dot)} />
      {label || status}
    </span>
  );
};
