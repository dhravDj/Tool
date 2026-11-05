import React from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  title,
  subtitle,
  action,
  children,
  className,
}) => {
  return (
    <div className={cn("p-6 max-w-7xl mx-auto space-y-6", className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{title}</h1>
          {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
        </div>
        {action && <div className="flex items-center gap-3">{action}</div>}
      </div>
      <div>{children}</div>
    </div>
  );
};
