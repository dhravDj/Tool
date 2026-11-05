import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Failed to load data",
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center text-foreground flex flex-col items-center justify-center gap-3",
        className
      )}
    >
      <AlertCircle className="h-8 w-8 text-rose-500" />
      <div>
        <h4 className="font-semibold text-rose-500">{title}</h4>
        <p className="text-sm text-muted-foreground mt-1 max-w-md">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 inline-flex items-center gap-2 rounded-lg bg-card px-4 py-2 text-sm font-medium border border-border shadow-sm hover:bg-muted transition"
        >
          <RefreshCw className="h-4 w-4" />
          Retry Connection
        </button>
      )}
    </div>
  );
};
