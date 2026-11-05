import React, { useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageContainer } from "@/components/ui/PageContainer";

export const ProcessingJobsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("all");

  const tabs = [
    { id: "all", label: "All Jobs", count: 0 },
    { id: "queued", label: "Queued", count: 0 },
    { id: "processing", label: "Processing", count: 0 },
    { id: "completed", label: "Completed", count: 0 },
    { id: "failed", label: "Failed", count: 0 },
  ];

  return (
    <PageContainer
      title="Processing Jobs"
      subtitle="Monitor document extraction tasks, worker queues, and batch execution states"
      action={
        <button
          onClick={() => {}}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      }
    >
      {/* Filtering Tabs */}
      <div className="flex border-b border-border gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 pb-3 px-3 text-xs font-medium border-b-2 transition ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <span>{tab.label}</span>
            <span className="rounded-full bg-muted px-1.5 py-0.2 text-[10px] font-mono">
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Jobs Container */}
      <div className="mt-6 rounded-xl border border-border bg-card p-6">
        <EmptyState
          icon={<Activity className="h-8 w-8" />}
          title="No Active Document Jobs"
          description="Document extraction jobs will appear here as parent batches and individual file workers execute."
        />
      </div>
    </PageContainer>
  );
};
