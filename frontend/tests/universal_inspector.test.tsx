import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UniversalFileInspector } from "../src/components/inspector/UniversalFileInspector";
import { ToastProvider } from "../src/context/ToastContext";
import { FileRecordSummary } from "../src/types/api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const mockFile: FileRecordSummary = {
  id: "test-file-uuid-12345",
  original_filename: "quarterly_earnings_report.pdf",
  stored_filename: "test-file-uuid-12345.pdf",
  extension: ".pdf",
  file_size: 1048576,
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  storage_path: "/data/storage/test-file-uuid-12345.pdf",
  status: "processed",
  created_at: new Date().toISOString(),
  detection_format_id: "pdf",
  claimed_extension: ".pdf",
  actual_extension: ".pdf",
  format_category: "document",
  detected_mime_type: "application/pdf",
  confidence_score: 0.99,
  confidence_level: "high",
  is_valid: true,
  is_mismatch: false,
  is_corrupted: false,
  is_suspicious: false,
};

describe("UniversalFileInspector Component", () => {
  it("renders file header, metadata pills, tabs, and format badge", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <BrowserRouter>
            <UniversalFileInspector file={mockFile} />
          </BrowserRouter>
        </ToastProvider>
      </QueryClientProvider>
    );

    // Filename and Category
    expect(screen.getAllByText("quarterly_earnings_report.pdf").length).toBeGreaterThan(0);
    expect(screen.getAllByText("PDF").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/document/i).length).toBeGreaterThan(0);

    // Tabs
    expect(screen.getByText("Intelligence Analysis")).toBeInTheDocument();
    expect(screen.getByText(/Chat & Ask AI/i)).toBeInTheDocument();
    expect(screen.getByText(/File Metadata & Hashes/i)).toBeInTheDocument();

    // Action buttons
    expect(screen.getByText("Index for AI")).toBeInTheDocument();
    expect(screen.getByText("Download")).toBeInTheDocument();
  });
});
