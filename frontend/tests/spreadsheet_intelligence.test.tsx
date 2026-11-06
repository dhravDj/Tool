import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SpreadsheetIntelligenceView } from "../src/components/SpreadsheetIntelligenceView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("SpreadsheetIntelligenceView Component", () => {
  it("renders spreadsheet intelligence inspector header and analyze trigger button", () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <SpreadsheetIntelligenceView
          fileId="test-sheet-uuid-1234"
          filename="quarterly_report.xlsx"
          format="xlsx"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("quarterly_report.xlsx")).toBeInTheDocument();
    expect(screen.getByText("xlsx")).toBeInTheDocument();
    expect(screen.getByText("Analyze Spreadsheet")).toBeInTheDocument();
  });
});
