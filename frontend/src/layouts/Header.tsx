import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Command,
  Menu,
  Plus,
  Search,
  User,
} from "lucide-react";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { api } from "@/services/api";
import { useUIStore } from "@/stores/uiStore";

export const Header: React.FC = () => {
  const { setMobileSidebarOpen } = useUIStore();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 15000,
    retry: 1,
  });

  const overallStatus = health?.status || "pending";

  const getPageTitle = (path: string): { title: string; category?: string } => {
    switch (path) {
      case "/":
        return { title: "Overview", category: "Workspace" };
      case "/upload":
        return { title: "Upload & Ingestion Gateway", category: "Workspace" };
      case "/files":
        return { title: "File Library & Explorer", category: "Workspace" };
      case "/ai":
        return { title: "Universal AI Workspace", category: "Intelligence" };
      case "/search":
        return { title: "Knowledge Search", category: "Intelligence" };
      case "/bulk-processing":
        return { title: "Bulk Processing Engine", category: "Scalability" };
      case "/jobs":
        return { title: "Processing Jobs & History", category: "Processing" };
      case "/system":
        return { title: "System Health & Capacity", category: "System" };
      case "/settings":
        return { title: "Platform Settings", category: "Preferences" };
      default:
        return { title: "DocuMind AI" };
    }
  };

  const { title, category } = getPageTitle(location.pathname);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-card/80 px-4 sm:px-6 backdrop-blur-md">
        {/* Left: Mobile Toggle & Breadcrumbs */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="p-2 lg:hidden text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2 truncate">
            {category && (
              <>
                <span className="hidden sm:inline text-xs text-muted-foreground font-medium">
                  {category}
                </span>
                <span className="hidden sm:inline text-xs text-muted-foreground/50">/</span>
              </>
            )}
            <h1 className="text-sm font-semibold text-foreground truncate tracking-tight">{title}</h1>
          </div>
        </div>

        {/* Center: Global Search / Command Bar */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
          <button
            type="button"
            onClick={() => setIsCommandOpen(true)}
            className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-xl border border-border bg-background hover:bg-muted/50 text-muted-foreground text-xs transition shadow-2xs group"
          >
            <span className="flex items-center gap-2">
              <Search className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
              <span>Search files, commands, or ask AI...</span>
            </span>
            <kbd className="inline-flex items-center gap-0.5 rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground border border-border">
              <Command className="h-2.5 w-2.5" /> K
            </kbd>
          </button>
        </div>

        {/* Right: Quick Upload, Gateway Health, Theme & Profile */}
        <div className="flex items-center gap-2.5">
          {/* Quick Upload Action */}
          <button
            onClick={() => navigate("/upload")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-primary/90 transition shadow-xs active:scale-[0.98]"
            title="Upload Files"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Upload</span>
          </button>

          {/* Subsystem Health Indicator */}
          <div className="hidden lg:flex items-center gap-2 text-xs px-2.5 py-1 rounded-xl bg-muted/60 border border-border/80">
            <span className="text-muted-foreground text-[11px]">System:</span>
            <StatusIndicator status={overallStatus} label={overallStatus.toUpperCase()} size="sm" />
          </div>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Tenant Avatar */}
          <div
            className="flex h-8 w-8 items-center justify-center rounded-xl bg-muted border border-border text-foreground font-semibold text-xs select-none"
            title="Current Session: Default Organization"
          >
            <User className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </header>

      {/* Global Command Palette */}
      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />
    </>
  );
};
