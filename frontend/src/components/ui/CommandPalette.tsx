import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Database,
  FileBox,
  FileCode,
  Files,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Layers,
  LayoutDashboard,
  Moon,
  Music,
  Package,
  Search,
  Settings,
  Sparkles,
  Sun,
  UploadCloud,
  Video,
} from "lucide-react";
import { api } from "@/services/api";
import { useUIStore } from "@/stores/uiStore";

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { theme, toggleTheme } = useUIStore();

  const { data: files } = useQuery({
    queryKey: ["files"],
    queryFn: () => api.getFiles(50, 0),
    enabled: isOpen,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (isOpen) {
          onClose();
        }
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const navCommands = useMemo(
    () => [
      {
        id: "nav-dash",
        title: "Overview Dashboard",
        category: "Navigation",
        icon: <LayoutDashboard className="h-4 w-4 text-blue-500" />,
        action: () => {
          navigate("/");
          onClose();
        },
      },
      {
        id: "nav-upload",
        title: "Upload & Detection Gateway",
        category: "Navigation",
        icon: <UploadCloud className="h-4 w-4 text-emerald-500" />,
        action: () => {
          navigate("/upload");
          onClose();
        },
      },
      {
        id: "nav-files",
        title: "File Library & Explorer",
        category: "Navigation",
        icon: <Files className="h-4 w-4 text-indigo-500" />,
        action: () => {
          navigate("/files");
          onClose();
        },
      },
      {
        id: "nav-ai",
        title: "Universal AI Workspace & Chat",
        category: "Navigation",
        icon: <Sparkles className="h-4 w-4 text-purple-500" />,
        action: () => {
          navigate("/ai");
          onClose();
        },
      },
      {
        id: "nav-search",
        title: "Knowledge Search (BM25 + Vector)",
        category: "Navigation",
        icon: <Search className="h-4 w-4 text-amber-500" />,
        action: () => {
          navigate("/search");
          onClose();
        },
      },
      {
        id: "nav-bulk",
        title: "Bulk Processing Engine",
        category: "Navigation",
        icon: <Layers className="h-4 w-4 text-indigo-500" />,
        action: () => {
          navigate("/bulk-processing");
          onClose();
        },
      },
      {
        id: "nav-jobs",
        title: "Processing Jobs & Activity History",
        category: "Navigation",
        icon: <Activity className="h-4 w-4 text-pink-500" />,
        action: () => {
          navigate("/jobs");
          onClose();
        },
      },
      {
        id: "nav-system",
        title: "System Telemetry & Hardware Status",
        category: "Navigation",
        icon: <Database className="h-4 w-4 text-sky-500" />,
        action: () => {
          navigate("/system");
          onClose();
        },
      },
      {
        id: "nav-settings",
        title: "Platform Settings & AI Providers",
        category: "Navigation",
        icon: <Settings className="h-4 w-4 text-slate-500" />,
        action: () => {
          navigate("/settings");
          onClose();
        },
      },
    ],
    [navigate, onClose]
  );

  const actionCommands = useMemo(
    () => [
      {
        id: "act-theme",
        title: `Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`,
        category: "Actions",
        icon:
          theme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          ),
        action: () => {
          toggleTheme();
          onClose();
        },
      },
    ],
    [theme, toggleTheme, onClose]
  );

  const filteredNav = navCommands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase())
  );

  const filteredFiles = (files || [])
    .filter(
      (f) =>
        f.original_filename.toLowerCase().includes(query.toLowerCase()) ||
        (f.detection_format_id &&
          f.detection_format_id.toLowerCase().includes(query.toLowerCase()))
    )
    .slice(0, 5);

  const getFileIcon = (cat?: string) => {
    switch (cat) {
      case "pdf":
      case "document":
        return <FileText className="h-4 w-4 text-blue-500" />;
      case "spreadsheet":
        return <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
      case "image":
        return <ImageIcon className="h-4 w-4 text-purple-500" />;
      case "audio":
        return <Music className="h-4 w-4 text-pink-500" />;
      case "video":
        return <Video className="h-4 w-4 text-red-500" />;
      case "archive":
        return <Package className="h-4 w-4 text-amber-500" />;
      case "code":
      case "structured_data":
        return <FileCode className="h-4 w-4 text-indigo-500" />;
      default:
        return <FileBox className="h-4 w-4 text-muted-foreground" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl rounded-2xl bg-card border border-border shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-150"
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 border-b border-border">
          <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search files..."
            className="w-full px-3 py-3.5 text-sm bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-hidden"
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-[10px] font-mono text-muted-foreground border border-border">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-3">
          {/* Quick Actions */}
          {actionCommands.length > 0 && (
            <div>
              <span className="px-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Actions
              </span>
              <div className="mt-1 space-y-0.5">
                {actionCommands.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={cmd.action}
                    className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-muted transition text-left"
                  >
                    <span className="flex items-center gap-2.5">
                      {cmd.icon}
                      {cmd.title}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Items */}
          {filteredNav.length > 0 && (
            <div>
              <span className="px-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Navigation
              </span>
              <div className="mt-1 space-y-0.5">
                {filteredNav.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={cmd.action}
                    className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-muted transition text-left"
                  >
                    <span className="flex items-center gap-2.5">
                      {cmd.icon}
                      {cmd.title}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* File Results */}
          {filteredFiles.length > 0 && (
            <div>
              <span className="px-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Files
              </span>
              <div className="mt-1 space-y-0.5">
                {filteredFiles.map((file) => (
                  <button
                    key={file.id}
                    onClick={() => {
                      navigate(`/files`);
                      onClose();
                    }}
                    className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs text-foreground hover:bg-muted transition text-left"
                  >
                    <span className="flex items-center gap-2.5 truncate">
                      {getFileIcon(file.format_category)}
                      <span className="font-medium truncate">{file.original_filename}</span>
                      <span className="text-[10px] text-muted-foreground uppercase font-mono">
                        {file.detection_format_id || file.extension}
                      </span>
                    </span>
                    <span className="text-[10px] text-muted-foreground capitalize shrink-0 ml-2">
                      {file.status}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {filteredNav.length === 0 && filteredFiles.length === 0 && (
            <div className="py-8 text-center text-xs text-muted-foreground">
              No matching commands or files found for &quot;{query}&quot;
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
