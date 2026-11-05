import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Menu } from "lucide-react";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { api } from "@/services/api";
import { useUIStore } from "@/stores/uiStore";

export const Header: React.FC = () => {
  const { setMobileSidebarOpen } = useUIStore();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 15000,
    retry: 1,
  });

  const overallStatus = health?.status || "pending";

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-card/80 px-4 sm:px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="p-2 lg:hidden text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg"
          aria-label="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border">
            Universal File Intelligence
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Subsystem Health Indicator */}
        <div className="hidden sm:flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">Gateway:</span>
          <StatusIndicator status={overallStatus} label={overallStatus.toUpperCase()} size="sm" />
        </div>

        {/* API Docs Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition"
          title="Open API Swagger Documentation"
        >
          <BookOpen className="h-4 w-4" />
          <span>API Docs</span>
        </a>

        {/* Theme Toggle */}
        <ThemeToggle />
      </div>
    </header>
  );
};
