import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentExtractionView } from "../src/components/DocumentExtractionView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("DocumentExtractionView Component", () => {
  it("renders document extraction view header and extract action button", () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <DocumentExtractionView
          fileId="test-file-uuid-1234"
          filename="quarterly_report.pdf"
          formatId="pdf"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("quarterly_report.pdf")).toBeInTheDocument();
    expect(screen.getByText("pdf")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Phase 3 Document Extraction: structure, tables, metadata, and reading order preservation."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Extract Content")).toBeInTheDocument();
    expect(screen.getByText("PDF Password (if protected):")).toBeInTheDocument();
    expect(
      screen.getByText("Extract embedded images to assets")
    ).toBeInTheDocument();
  });
});
