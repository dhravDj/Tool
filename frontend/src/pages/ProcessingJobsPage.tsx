import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  History,
  Loader2,
  RefreshCw,
  RotateCcw,
  Search,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Modal } from "@/components/ui/Modal";
import { PageContainer } from "@/components/ui/PageContainer";
import { useToast } from "@/context/ToastContext";
import { api } from "@/services/api";
import { JobAttempt, ProcessingJob } from "@/types/api";

export const ProcessingJobsPage: React.FC = () => {
  const { success, error: toastError } = useToast();
  const [activeStatus, setActiveStatus] = useState<string>("all");
  const [selectedStage, setSelectedStage] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedJobForAttempts, setSelectedJobForAttempts] = useState<ProcessingJob | null>(null);

  // Queries
  const {
    data: jobs,
    isLoading: isJobsLoading,
    error: jobsError,
    refetch: refetchJobs,
    isFetching,
  } = useQuery({
    queryKey: ["jobs", activeStatus, selectedStage],
    queryFn: () =>
      api.getJobs({
        status: activeStatus === "all" ? undefined : activeStatus,
        stage: selectedStage === "all" ? undefined : selectedStage,
        limit: 100,
      }),
    refetchInterval: 5000,
  });

  const { data: queueStatus } = useQuery({
    queryKey: ["queueStatus"],
    queryFn: api.getQueueStatus,
    refetchInterval: 5000,
  });

  // Attempts Query
  const { data: attempts, isLoading: isAttemptsLoading } = useQuery({
    queryKey: ["jobAttempts", selectedJobForAttempts?.id],
    queryFn: () =>
      selectedJobForAttempts ? api.getJobAttempts(selectedJobForAttempts.id) : Promise.resolve([]),
    enabled: Boolean(selectedJobForAttempts),
  });

  const handleRetryJob = async (jobId: string) => {
    try {
      await api.retryJob(jobId);
      success("Job Requeued", "Task has been resubmitted to the priority queue.");
      refetchJobs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Retry failed.";
      toastError("Retry Error", msg);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await api.cancelJob(jobId);
      success("Job Cancelled", "Task has been revoked.");
      refetchJobs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Cancel failed.";
      toastError("Cancellation Error", msg);
    }
  };

  const filteredJobs = (jobs || []).filter((j: ProcessingJob) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      j.id.toLowerCase().includes(term) ||
      (j.filename && j.filename.toLowerCase().includes(term)) ||
      j.job_type.toLowerCase().includes(term) ||
      j.stage.toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="success" size="sm">Completed</Badge>;
      case "processing":
        return (
          <Badge variant="primary" size="sm">
            <Loader2 className="h-3 w-3 animate-spin mr-1" /> Processing
          </Badge>
        );
      case "queued":
        return <Badge variant="warning" size="sm">Queued</Badge>;
      case "failed":
        return <Badge variant="danger" size="sm">Failed</Badge>;
      case "cancelled":
        return <Badge variant="default" size="sm">Cancelled</Badge>;
      default:
        return <Badge variant="outline" size="sm">{status}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Processing Jobs & Activity History"
      subtitle="Real-time execution telemetry, priority queues, and attempt failure logs"
      action={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchJobs()}
            isLoading={isFetching}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh
          </Button>
        </div>
      }
    >
      {/* Real-time Queue Depth Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="rounded-2xl border border-border bg-card p-4 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Interactive (80+)
          </span>
          <p className="text-xl font-mono font-bold text-foreground mt-1">
            {queueStatus?.queues?.interactive ?? 0}
          </p>
          <span className="text-[10px] text-muted-foreground">SLA &lt; 2.0s</span>
        </div>

        <div className="rounded-2xl border border-border bg-card p-4 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Normal (50..79)
          </span>
          <p className="text-xl font-mono font-bold text-foreground mt-1">
            {queueStatus?.queues?.normal ?? 0}
          </p>
          <span className="text-[10px] text-muted-foreground">Standard Queue</span>
        </div>

        <div className="rounded-2xl border border-border bg-card p-4 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Bulk (20..49)
          </span>
          <p className="text-xl font-mono font-bold text-foreground mt-1">
            {queueStatus?.queues?.bulk ?? 0}
          </p>
          <span className="text-[10px] text-muted-foreground">Batch Ingestion</span>
        </div>

        <div className="rounded-2xl border border-border bg-card p-4 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            In Flight
          </span>
          <p className="text-xl font-mono font-bold text-blue-500 mt-1">
            {queueStatus?.total_processing ?? 0}
          </p>
          <span className="text-[10px] text-muted-foreground">
            {queueStatus?.active_workers_count ?? 0} workers active
          </span>
        </div>

        <div className="rounded-2xl border border-border bg-card p-4 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Dead Letter (DLQ)
          </span>
          <p className="text-xl font-mono font-bold text-red-500 mt-1">
            {queueStatus?.total_dead_letter ?? 0}
          </p>
          <span className="text-[10px] text-muted-foreground">Exhausted Retries</span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mt-6 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by job ID, filename, or stage..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-border bg-card pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Tabs */}
          <div className="flex rounded-xl bg-muted/60 p-1 border border-border shadow-2xs">
            {["all", "queued", "processing", "completed", "failed", "cancelled"].map((st) => (
              <button
                key={st}
                onClick={() => setActiveStatus(st)}
                className={`px-2.5 py-1 text-xs font-medium rounded-lg capitalize transition-all ${
                  activeStatus === st
                    ? "bg-card text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Stage Dropdown */}
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="text-xs px-2.5 py-1.5 rounded-xl border border-border bg-card text-foreground focus:outline-hidden shadow-2xs"
          >
            <option value="all">All Stages</option>
            <option value="registration">Registration</option>
            <option value="detection">Detection</option>
            <option value="extraction">Extraction</option>
            <option value="ai_indexing">AI Indexing</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Jobs Table Container */}
      <div className="mt-4 rounded-2xl border border-border bg-card overflow-hidden shadow-2xs">
        {isJobsLoading ? (
          <LoadingState message="Fetching active pipeline jobs..." />
        ) : jobsError ? (
          <ErrorState
            title="Failed to Load Jobs"
            message={jobsError instanceof Error ? jobsError.message : "Unable to reach jobs API."}
            onRetry={() => refetchJobs()}
          />
        ) : filteredJobs.length === 0 ? (
          <EmptyState
            icon={<Activity className="h-8 w-8" />}
            title="No Matching Jobs Found"
            description="Processing jobs will appear here as file uploads and batch pipelines execute."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/30 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Job ID &amp; Target</th>
                  <th className="px-4 py-3">Stage</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Retries</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredJobs.map((job: ProcessingJob) => (
                  <tr key={job.id} className="hover:bg-muted/30 transition">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-foreground truncate max-w-xs">
                        {job.filename || job.file_id || "Standalone Task"}
                      </div>
                      <span className="font-mono text-[10px] text-muted-foreground block truncate">
                        ID: {job.id}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono uppercase text-[11px] font-medium bg-muted px-2 py-0.5 rounded text-foreground">
                        {job.stage}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs">{job.priority}</span>
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(job.status)}</td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-muted-foreground">
                        {job.retry_count} / {job.max_retries}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {job.created_at ? new Date(job.created_at).toLocaleTimeString() : "N/A"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedJobForAttempts(job)}
                          title="View Execution History"
                          aria-label="View Execution History"
                        >
                          <History className="h-3.5 w-3.5" />
                        </Button>

                        {job.status === "failed" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRetryJob(job.id)}
                            title="Retry Failed Job"
                            aria-label="Retry Failed Job"
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Retry
                          </Button>
                        )}

                        {(job.status === "queued" || job.status === "processing") && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleCancelJob(job.id)}
                            title="Cancel Job"
                            aria-label="Cancel Job"
                          >
                            Cancel
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Attempt History Modal */}
      <Modal
        isOpen={Boolean(selectedJobForAttempts)}
        onClose={() => setSelectedJobForAttempts(null)}
        title={
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-primary" />
            <span>Job Execution Audit History</span>
          </div>
        }
        description={`Attempt logs and worker traces for job ${selectedJobForAttempts?.id}`}
        maxWidth="xl"
      >
        {isAttemptsLoading ? (
          <LoadingState message="Loading attempt traces..." />
        ) : !attempts || attempts.length === 0 ? (
          <div className="py-8 text-center text-xs text-muted-foreground">
            No execution attempts logged yet for this task.
          </div>
        ) : (
          <div className="space-y-3">
            {attempts.map((att: JobAttempt) => (
              <div
                key={att.id}
                className="p-3.5 rounded-xl border border-border bg-background space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground">
                      Attempt #{att.attempt_number}
                    </span>
                    <Badge variant={att.status === "success" ? "success" : "danger"} size="sm">
                      {att.status.toUpperCase()}
                    </Badge>
                  </div>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {att.duration_ms ? `${att.duration_ms.toFixed(1)} ms` : "N/A"}
                  </span>
                </div>

                <div className="text-[11px] text-muted-foreground">
                  <span>Worker: </span>
                  <span className="font-mono text-foreground">{att.worker_id || "unassigned"}</span>
                </div>

                {att.error_message && (
                  <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 font-mono text-[10px] whitespace-pre-wrap">
                    {att.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </PageContainer>
  );
};
