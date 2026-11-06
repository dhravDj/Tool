import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AIWorkspace } from "../src/components/ai/AIWorkspace";
import { CitationViewer } from "../src/components/ai/CitationViewer";
import { api } from "../src/services/api";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("AI Intelligence Frontend Components", () => {
  it("renders AIWorkspace tabs and switches between them", async () => {
    const queryClient = createTestQueryClient();

    vi.spyOn(api, "getAISettings").mockResolvedValue({
      default_provider: "sovereign",
      cloud_consent_given: false,
      ollama_base_url: "http://localhost:11434",
    });

    vi.spyOn(api, "getAITelemetry").mockResolvedValue({
      total_tokens_used: 12500,
      total_inference_calls: 42,
      average_latency_ms: 18.5,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <AIWorkspace selectedFileId="test-file-123" selectedFilename="sample.pdf" />
      </QueryClientProvider>
    );

    // Initial tab: File Chat
    expect(screen.getByText("Cross-Modal File Intelligence")).toBeInTheDocument();
    expect(screen.getByText("sample.pdf")).toBeInTheDocument();

    // Click Hybrid Knowledge Search
    fireEvent.click(screen.getByText("Hybrid Knowledge Search"));
    expect(
      screen.getByPlaceholderText("Search across all indexed files, schemas, transcripts, and code...")
    ).toBeInTheDocument();

    // Click Summaries & Compare
    fireEvent.click(screen.getByText("Summaries & Compare"));
    expect(screen.getByText("Single-File Multi-Type Summarization")).toBeInTheDocument();
    expect(screen.getByText("Cross-File Comparison & Contradiction Detection")).toBeInTheDocument();

    // Click AI Settings
    fireEvent.click(screen.getByText("AI Settings"));
    expect(screen.getByText("Default Sovereign Architecture & Privacy Guarantee")).toBeInTheDocument();
    expect(screen.getByText("Sovereign Engine (Default)")).toBeInTheDocument();
  });

  it("renders CitationViewer with formatted citations and expands on click", async () => {
    const dummyCitations = [
      {
        citation_id: "[1]",
        file_id: "fid-123",
        filename: "financial_report.pdf",
        source_type: "document",
        formatted_citation: "financial_report.pdf — Page 14",
        snippet: "Net income expanded by 24% year-over-year.",
        page_number: 14,
      },
    ];

    render(<CitationViewer citations={dummyCitations} />);

    expect(screen.getByText("Verified Grounded Sources (1)")).toBeInTheDocument();
    expect(screen.getByText("financial_report.pdf — Page 14")).toBeInTheDocument();
    expect(screen.getByText(/Net income expanded by 24%/)).toBeInTheDocument();

    // Click to expand details
    fireEvent.click(screen.getByText("financial_report.pdf — Page 14"));
    expect(screen.getByText("financial_report.pdf")).toBeInTheDocument();
  });
});
