import React, { useState } from "react";
import { Layers, Upload, Clock, Activity } from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { BulkUploadView } from "@/components/bulk/BulkUploadView";
import { BatchProcessingView } from "@/components/bulk/BatchProcessingView";
import { JobMonitorView } from "@/components/bulk/JobMonitorView";
import { ProcessingAnalyticsView } from "@/components/bulk/ProcessingAnalyticsView";

export const BulkProcessingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"upload" | "batches" | "jobs" | "analytics">("upload");

  return (
    <PageContainer
      title="Bulk Processing & Scalability Engine"
      subtitle="Large-scale file ingestion, prioritized asynchronous queueing, multi-worker pipelines, and real-time telemetry."
      action={
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 text-xs font-semibold">
          <Layers className="h-4 w-4" />
          <span>Multi-Tier Concurrency</span>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Navigation Tabs */}
        <div className="flex border-b border-border space-x-1 sm:space-x-4">
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex items-center space-x-2 py-3 px-3 sm:px-4 text-xs sm:text-sm font-medium border-b-2 transition-colors ${
              activeTab === "upload"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Ingestion & Upload</span>
          </button>

          <button
            onClick={() => setActiveTab("batches")}
            className={`flex items-center space-x-2 py-3 px-3 sm:px-4 text-xs sm:text-sm font-medium border-b-2 transition-colors ${
              activeTab === "batches"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Batches</span>
          </button>

          <button
            onClick={() => setActiveTab("jobs")}
            className={`flex items-center space-x-2 py-3 px-3 sm:px-4 text-xs sm:text-sm font-medium border-b-2 transition-colors ${
              activeTab === "jobs"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Job Monitor</span>
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`flex items-center space-x-2 py-3 px-3 sm:px-4 text-xs sm:text-sm font-medium border-b-2 transition-colors ${
              activeTab === "analytics"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Telemetry & Capacity</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "upload" && <BulkUploadView onBatchCreated={() => setActiveTab("batches")} />}
        {activeTab === "batches" && <BatchProcessingView />}
        {activeTab === "jobs" && <JobMonitorView />}
        {activeTab === "analytics" && <ProcessingAnalyticsView />}
      </div>
    </PageContainer>
  );
};
