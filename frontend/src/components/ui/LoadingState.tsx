import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading platform data...",
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 gap-3", className)}>
      <Loader2 className="h-7 w-7 animate-spin text-primary" />
      <span className="text-sm font-medium text-muted-foreground">{message}</span>
    </div>
  );
};
