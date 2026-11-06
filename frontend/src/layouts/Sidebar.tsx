import React from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Files,
  Layers,
  LayoutDashboard,
  Server,
  Settings,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";

export const Sidebar: React.FC = () => {
  const {
    isSidebarCollapsed,
    toggleSidebar,
    isMobileSidebarOpen,
    setMobileSidebarOpen,
  } = useUIStore();

  const navItems = [
    { label: "Dashboard", path: "/", icon: <LayoutDashboard className="h-5 w-5" /> },
    { label: "Upload & Ingest", path: "/upload", icon: <UploadCloud className="h-5 w-5" /> },
    { label: "Bulk Processing", path: "/bulk-processing", icon: <Layers className="h-5 w-5 text-indigo-500" /> },
    { label: "Processing Jobs", path: "/jobs", icon: <Activity className="h-5 w-5" /> },
    { label: "File Library", path: "/files", icon: <Files className="h-5 w-5" /> },
    { label: "AI Intelligence", path: "/ai", icon: <Sparkles className="h-5 w-5 text-blue-500" /> },
    { label: "System Status", path: "/system", icon: <Server className="h-5 w-5" /> },
    { label: "Settings", path: "/settings", icon: <Settings className="h-5 w-5" /> },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-300 lg:static",
          isSidebarCollapsed ? "w-20" : "w-64",
          isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-white font-bold">
              <Cpu className="h-5 w-5" />
            </div>
            {!isSidebarCollapsed && (
              <div className="flex flex-col truncate">
                <span className="font-bold text-sm tracking-tight text-foreground">DocuMind AI</span>
                <span className="text-[10px] text-muted-foreground uppercase font-mono">Phase 1 Core</span>
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="lg:hidden text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setMobileSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                  isActive
                    ? "bg-primary text-white"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  isSidebarCollapsed && "justify-center px-0"
                )
              }
              title={isSidebarCollapsed ? item.label : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!isSidebarCollapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Collapse toggle (desktop only) */}
        <div className="hidden lg:flex p-3 border-t border-border">
          <button
            onClick={toggleSidebar}
            className="flex w-full items-center justify-center gap-2 rounded-lg p-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition"
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Collapse Sidebar</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
};
