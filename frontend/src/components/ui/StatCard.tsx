import React from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: React.ReactNode;
  trend?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  trend,
  className,
}) => {
  return (
    <div
      className={cn(
        "bg-card text-card-foreground border border-border rounded-xl p-5 shadow-sm transition hover:shadow-md",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        <div className="p-2 bg-muted/60 text-foreground rounded-lg">{icon}</div>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-foreground">{value}</span>
        {trend && <span className="text-xs font-semibold text-emerald-500">{trend}</span>}
      </div>
      {subtext && <p className="mt-1 text-xs text-muted-foreground">{subtext}</p>}
    </div>
  );
};
