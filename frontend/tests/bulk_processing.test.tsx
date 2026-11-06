import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BulkUploadView } from "../src/components/bulk/BulkUploadView";
import { BatchProcessingView } from "../src/components/bulk/BatchProcessingView";
import { JobMonitorView } from "../src/components/bulk/JobMonitorView";
import { ProcessingAnalyticsView } from "../src/components/bulk/ProcessingAnalyticsView";
import { api } from "../src/services/api";

describe("Bulk Processing & Scalability Engine Components (Phase 12)", () => {
  it("renders BulkUploadView with options, file selection, and drag zone", () => {
    render(<BulkUploadView />);
    expect(screen.getByText("High-Volume File Ingestion")).toBeInTheDocument();
    expect(screen.getByText("Queue Priority Tier")).toBeInTheDocument();
    expect(screen.getByText("Browse Files")).toBeInTheDocument();
    expect(screen.getByText("Select Directory Folder")).toBeInTheDocument();
  });

  it("renders BatchProcessingView with batches, progress, and controls", async () => {
    vi.spyOn(api, "listBatches").mockResolvedValue([
      {
        id: "batch-12345678-abcd",
        name: "Q4 Tax Audit Batch",
        status: "processing",
        total_files: 250,
        accepted_files: 250,
        rejected_files: 0,
        queued_files: 50,
        processing_files: 100,
        completed_files: 95,
        partially_completed_files: 0,
        failed_files: 5,
        cancelled_files: 0,
        total_size_bytes: 52428800,
        overall_progress: 58.5,
        processing_policy: { priority: 50 },
        error_summary: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(<BatchProcessingView />);

    await waitFor(() => {
      expect(screen.getByText("Q4 Tax Audit Batch")).toBeInTheDocument();
      expect(screen.getAllByText("Processing").length).toBeGreaterThan(0);
      expect(screen.getByText("58.5%")).toBeInTheDocument();
      expect(screen.getByText("Pause")).toBeInTheDocument();
      expect(screen.getByText("Cancel")).toBeInTheDocument();
      expect(screen.getByText("Retry Failed (5)")).toBeInTheDocument();
    });
  });

  it("renders JobMonitorView with queue depths and jobs list", async () => {
    vi.spyOn(api, "getQueueStatus").mockResolvedValue({
      queues: { interactive: 2, normal: 15, bulk: 120, maintenance: 0 },
      total_queued: 137,
      total_processing: 4,
      total_dead_letter: 1,
      avg_latency_ms: 0.45,
      active_workers_count: 4,
      timestamp: new Date().toISOString(),
    });

    vi.spyOn(api, "listJobs").mockResolvedValue([
      {
        id: "job-1111",
        batch_id: "batch-1",
        file_id: "file-99",
        filename: "statement.pdf",
        job_type: "pipeline_orchestration",
        stage: "extraction",
        priority: 50,
        status: "processing",
        current_worker_id: "worker-01",
        retry_count: 0,
        max_retries: 3,
        progress: 60.0,
        stage_progress: {},
        idempotency_key: "batch_1_file_99",
        created_at: new Date().toISOString(),
      },
    ]);

    render(<JobMonitorView />);

    await waitFor(() => {
      expect(screen.getByText("Priority Queue Depths & Backlog")).toBeInTheDocument();
      expect(screen.getByText("Interactive (80+)")).toBeInTheDocument();
      expect(screen.getByText("Dead Letter (DLQ)")).toBeInTheDocument();
      expect(screen.getByText("statement.pdf")).toBeInTheDocument();
      expect(screen.getByText("extraction")).toBeInTheDocument();
    });
  });

  it("renders ProcessingAnalyticsView with hardware metrics and workers", async () => {
    vi.spyOn(api, "getSystemCapacity").mockResolvedValue({
      host_info: { cpu: { logical_cores: 16 } },
      max_parallel_cpu_workers: 4,
      max_concurrent_gpu_slots: 1,
      active_cpu_slots_in_use: 2,
      active_gpu_slots_in_use: 0,
      submission_capacity_files_per_sec: 500,
      detection_capacity_files_per_sec: 480,
      extraction_capacity_files_per_sec: 50,
      ai_indexing_capacity_chunks_per_sec: 450,
      is_under_backpressure: false,
      evaluated_at: new Date().toISOString(),
    });

    vi.spyOn(api, "getWorkerStatus").mockResolvedValue([
      {
        worker_id: "worker-node-alpha",
        hostname: "documind-linux",
        pid: 12345,
        worker_type: "generic",
        jobs_completed: 420,
        jobs_failed: 2,
        cpu_percent: 18.5,
        memory_mb: 245.0,
        status: "alive",
        last_heartbeat: new Date().toISOString(),
        started_at: new Date().toISOString(),
      },
    ]);

    vi.spyOn(api, "getResourceUsage").mockResolvedValue({
      cpu: { logical_cores: 16, recommended_workers: 4, active_workers_limit: 4 },
      memory: { total_ram_mb: 16384, free_ram_mb: 8192 },
      gpu: { available: true, name: "NVIDIA GeForce RTX 3050 Laptop GPU" },
      storage: { total_gb: 500, used_gb: 120, free_gb: 380, percent_used: 24.0 },
      timestamp: new Date().toISOString(),
    });

    render(<ProcessingAnalyticsView />);

    await waitFor(() => {
      expect(screen.getByText("System Processing Capacity")).toBeInTheDocument();
      expect(screen.getByText("4 slots")).toBeInTheDocument();
      expect(screen.getByText("1 slot")).toBeInTheDocument();
      expect(screen.getByText("Host Hardware Telemetry")).toBeInTheDocument();
      expect(screen.getByText("worker-node-alpha")).toBeInTheDocument();
    });
  });
});
