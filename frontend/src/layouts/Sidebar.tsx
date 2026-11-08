import React from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Cpu,
  RefreshCw,
  Server,
  Settings,
  X,
} from "lucide-react";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";

interface NavGroup {
  name: string;
  items: Array<{
    label: string;
    path: string;
    icon: React.ReactNode;
    badge?: string;
  }>;
}

export const Sidebar: React.FC = () => {
  const {
    isSidebarCollapsed,
    toggleSidebar,
    isMobileSidebarOpen,
    setMobileSidebarOpen,
  } = useUIStore();

  const navGroups: NavGroup[] = [
    {
      name: "File Converter",
      items: [
        { label: "Bulk Converter", path: "/", icon: <RefreshCw className="h-4.5 w-4.5 text-blue-500" /> },
        { label: "Conversion History", path: "/history", icon: <Activity className="h-4.5 w-4.5 text-emerald-500" /> },
      ],
    },
    {
      name: "System",
      items: [
        { label: "System Status", path: "/system", icon: <Server className="h-4.5 w-4.5 text-sky-500" /> },
        { label: "Settings", path: "/settings", icon: <Settings className="h-4.5 w-4.5 text-slate-500" /> },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden backdrop-blur-xs"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-300 lg:static select-none",
          isSidebarCollapsed ? "w-18" : "w-64",
          isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-white font-bold shadow-xs">
              <Cpu className="h-5 w-5" />
            </div>
            {!isSidebarCollapsed && (
              <div className="flex flex-col truncate">
                <span className="font-bold text-sm tracking-tight text-foreground">DocuMind AI</span>
                <span className="text-[10px] text-muted-foreground uppercase font-mono tracking-wider">
                  Universal SaaS
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="lg:hidden text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-muted"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Groups */}
        <nav className="flex-1 space-y-4 p-3 overflow-y-auto">
          {navGroups.map((group) => (
            <div key={group.name} className="space-y-1">
              {!isSidebarCollapsed && (
                <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/80">
                  {group.name}
                </div>
              )}
              {group.items.map((item) => {
                const linkContent = (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileSidebarOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all group",
                        isActive
                          ? "bg-primary text-white shadow-xs"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        isSidebarCollapsed && "justify-center px-0 h-10 w-10 mx-auto"
                      )
                    }
                  >
                    <span className="shrink-0 group-hover:scale-105 transition-transform">
                      {item.icon}
                    </span>
                    {!isSidebarCollapsed && <span className="truncate">{item.label}</span>}
                  </NavLink>
                );

                return isSidebarCollapsed ? (
                  <Tooltip key={item.path} content={item.label} side="right">
                    {linkContent}
                  </Tooltip>
                ) : (
                  linkContent
                );
              })}
            </div>
          ))}
        </nav>

        {/* Collapse toggle (desktop only) */}
        <div className="hidden lg:flex p-3 border-t border-border">
          <button
            onClick={toggleSidebar}
            className="flex w-full items-center justify-center gap-2 rounded-xl p-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition"
            aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Collapse Navigation</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
};
