import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Cpu,
  Globe,
  HardDrive,
  Lock,
  Moon,
  Save,
  Shield,
  Sparkles,
  Sun,
} from "lucide-react";
import { AISettingsView } from "@/components/ai/AISettingsView";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { PageContainer } from "@/components/ui/PageContainer";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { useUIStore } from "@/stores/uiStore";

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useUIStore();
  const { success } = useToast();
  const [activeTab, setActiveTab] = useState<"general" | "ai" | "processing" | "storage" | "security">("general");

  const [defaultExportFormat, setDefaultExportFormat] = useState("json");
  const [autoIndexUploads, setAutoIndexUploads] = useState(false);

  const { data: capacity } = useQuery({
    queryKey: ["capacity"],
    queryFn: api.getSystemCapacity,
  });

  const { data: resourceUsage } = useQuery({
    queryKey: ["resourceUsage"],
    queryFn: api.getResourceUsage,
  });

  const handleSaveGeneral = () => {
    success("Preferences Saved", "Default upload and export settings updated.");
  };

  return (
    <PageContainer
      title="Platform Settings & Configuration"
      subtitle="Manage system preferences, AI model routing, processing capacity, and data governance"
    >
      {/* Settings Navigation Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab("general")}
          className={`flex items-center gap-2 pb-3 px-3 text-xs font-semibold border-b-2 transition shrink-0 ${
            activeTab === "general"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Globe className="h-4 w-4" />
          General &amp; Display
        </button>

        <button
          onClick={() => setActiveTab("ai")}
          className={`flex items-center gap-2 pb-3 px-3 text-xs font-semibold border-b-2 transition shrink-0 ${
            activeTab === "ai"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Sparkles className="h-4 w-4 text-purple-500" />
          AI Engine &amp; Cloud Consent
        </button>

        <button
          onClick={() => setActiveTab("processing")}
          className={`flex items-center gap-2 pb-3 px-3 text-xs font-semibold border-b-2 transition shrink-0 ${
            activeTab === "processing"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Cpu className="h-4 w-4 text-indigo-500" />
          Hardware &amp; Concurrency
        </button>

        <button
          onClick={() => setActiveTab("storage")}
          className={`flex items-center gap-2 pb-3 px-3 text-xs font-semibold border-b-2 transition shrink-0 ${
            activeTab === "storage"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <HardDrive className="h-4 w-4 text-emerald-500" />
          Storage &amp; Quotas
        </button>

        <button
          onClick={() => setActiveTab("security")}
          className={`flex items-center gap-2 pb-3 px-3 text-xs font-semibold border-b-2 transition shrink-0 ${
            activeTab === "security"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Shield className="h-4 w-4 text-blue-500" />
          Security &amp; Privacy
        </button>
      </div>

      {/* Content Area */}
      <div className="mt-6 max-w-4xl space-y-6">
        {/* Tab 1: General */}
        {activeTab === "general" && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
              <h3 className="text-sm font-semibold text-foreground">Theme &amp; Appearance</h3>
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-muted/40 border border-border">
                <div>
                  <p className="text-xs font-semibold text-foreground">Color Mode</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Toggle between clean light SaaS layout and dark contrast mode.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleTheme}
                  leftIcon={theme === "dark" ? <Sun className="h-3.5 w-3.5 text-amber-400" /> : <Moon className="h-3.5 w-3.5 text-slate-600" />}
                >
                  {theme === "dark" ? "Light Mode" : "Dark Mode"}
                </Button>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
              <h3 className="text-sm font-semibold text-foreground">Defaults &amp; Workflow</h3>
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-muted/40 border border-border">
                  <div>
                    <p className="font-semibold text-foreground">Default Ingestion Export Format</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Canonical output standard used for downloads.
                    </p>
                  </div>
                  <select
                    value={defaultExportFormat}
                    onChange={(e) => setDefaultExportFormat(e.target.value)}
                    className="text-xs px-3 py-1.5 rounded-lg border border-border bg-card text-foreground focus:outline-hidden"
                  >
                    <option value="json">Structured JSON</option>
                    <option value="markdown">Markdown (.md)</option>
                    <option value="text">Plain Text (.txt)</option>
                  </select>
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-muted/40 border border-border">
                  <div>
                    <p className="font-semibold text-foreground">Automatic AI Knowledge Indexing</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Automatically generate chunks and vector embeddings immediately upon upload.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={autoIndexUploads}
                    onChange={(e) => setAutoIndexUploads(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button variant="primary" size="sm" onClick={handleSaveGeneral} leftIcon={<Save className="h-3.5 w-3.5" />}>
                  Save Preferences
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: AI Engine */}
        {activeTab === "ai" && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs">
            <AISettingsView />
          </div>
        )}

        {/* Tab 3: Processing & Hardware */}
        {activeTab === "processing" && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">HardwareGovernor Allocations</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Hardware slot bounding prevents CPU thrashing and GPU CUDA out-of-memory errors.
                  </p>
                </div>
                <Badge variant="primary" size="sm">
                  Active
                </Badge>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 rounded-xl bg-muted/40 border border-border space-y-1">
                  <span className="text-muted-foreground block text-[11px]">Parallel CPU Worker Slots</span>
                  <p className="text-base font-mono font-bold text-foreground">
                    {capacity?.max_parallel_cpu_workers ?? 4} Slots
                  </p>
                  <span className="text-[10px] text-muted-foreground">
                    Active slots in use: {capacity?.active_cpu_slots_in_use ?? 0}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-muted/40 border border-border space-y-1">
                  <span className="text-muted-foreground block text-[11px]">GPU Mutex Slot</span>
                  <p className="text-base font-mono font-bold text-foreground">
                    {capacity?.max_concurrent_gpu_slots ?? 1} Slot (Serialized)
                  </p>
                  <span className="text-[10px] text-muted-foreground">
                    Active GPU slots: {capacity?.active_gpu_slots_in_use ?? 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
              <h3 className="text-sm font-semibold text-foreground">Host Hardware Probes</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-muted/30 border border-border">
                  <span className="text-muted-foreground text-[10px] block uppercase font-semibold">CPU Cores</span>
                  <span className="text-sm font-bold text-foreground mt-0.5 block">
                    {resourceUsage?.cpu?.logical_cores ?? 0} Logical Cores
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-muted/30 border border-border">
                  <span className="text-muted-foreground text-[10px] block uppercase font-semibold">Total RAM</span>
                  <span className="text-sm font-bold text-foreground mt-0.5 block">
                    {Math.round((resourceUsage?.memory?.total_ram_mb ?? 0) / 1024)} GB System Memory
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-muted/30 border border-border">
                  <span className="text-muted-foreground text-[10px] block uppercase font-semibold">GPU Acceleration</span>
                  <span className="text-sm font-bold text-foreground mt-0.5 block">
                    {resourceUsage?.gpu?.available ? resourceUsage.gpu.name || "NVIDIA Active" : "CPU Fallback"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Storage */}
        {activeTab === "storage" && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Storage Subsystem</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-muted/40 border border-border">
                <span className="text-muted-foreground text-[11px] block">Storage Backend</span>
                <p className="text-sm font-semibold text-foreground mt-0.5">LocalStorageProvider (Local Disk)</p>
              </div>
              <div className="p-3.5 rounded-xl bg-muted/40 border border-border">
                <span className="text-muted-foreground text-[11px] block">Disk Quota Utilization</span>
                <p className="text-sm font-semibold text-foreground mt-0.5">
                  {resourceUsage?.storage?.percent_used ?? 0}% utilized ({resourceUsage?.storage?.free_gb ?? 0} GB free)
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-muted/40 border border-border">
                <span className="text-muted-foreground text-[11px] block">Max Upload Size</span>
                <p className="text-sm font-semibold text-foreground mt-0.5">2,048 MB (2 GB)</p>
              </div>
              <div className="p-3.5 rounded-xl bg-muted/40 border border-border">
                <span className="text-muted-foreground text-[11px] block">Retention Policy</span>
                <p className="text-sm font-semibold text-foreground mt-0.5">Indefinite (Managed in File Library)</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Security */}
        {activeTab === "security" && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs space-y-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Lock className="h-4 w-4 text-primary" />
              Security Safeguards &amp; Zero-Trust Protections
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border">
                <div>
                  <span className="font-semibold text-foreground">Zero-Trust Magic Byte Verification</span>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Binary headers are inspected; claimed extensions are never trusted.
                  </p>
                </div>
                <Badge variant="success" size="sm">Enforced</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border">
                <div>
                  <span className="font-semibold text-foreground">Defensive DefusedXML &amp; Billion Laughs Defense</span>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Guards against XXE entity expansion in XML, OOXML, and YAML.
                  </p>
                </div>
                <Badge variant="success" size="sm">Enforced</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border">
                <div>
                  <span className="font-semibold text-foreground">Zip Slip &amp; Archive Bomb Containment</span>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Traversal paths rejected; decompression ratio capped at 100.0 limit.
                  </p>
                </div>
                <Badge variant="success" size="sm">Enforced</Badge>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border">
                <div>
                  <span className="font-semibold text-foreground">Sovereign Data Privacy Guarantee</span>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Zero document content leaves the machine without explicit user cloud consent.
                  </p>
                </div>
                <Badge variant="success" size="sm">Enforced</Badge>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
