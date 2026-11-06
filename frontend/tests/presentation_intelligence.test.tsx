import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PresentationIntelligenceView } from "../src/components/PresentationIntelligenceView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("PresentationIntelligenceView Component", () => {
  it("renders presentation intelligence inspector header and analyze trigger button", () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <PresentationIntelligenceView
          fileId="test-pres-uuid-5678"
          filename="strategy_deck.pptx"
          format="pptx"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("strategy_deck.pptx")).toBeInTheDocument();
    expect(screen.getByText("pptx")).toBeInTheDocument();
    expect(screen.getByText("Analyze Presentation")).toBeInTheDocument();
  });
});
