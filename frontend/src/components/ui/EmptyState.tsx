import React from "react";
import { FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-border bg-card/50",
        className
      )}
    >
      <div className="p-3 bg-muted rounded-full text-muted-foreground mb-4">
        {icon || <FolderOpen className="h-8 w-8" />}
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};
