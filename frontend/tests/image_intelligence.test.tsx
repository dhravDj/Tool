import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ImageIntelligenceView } from "../src/components/ImageIntelligenceView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("ImageIntelligenceView Component", () => {
  it("renders image intelligence inspector header and analyze trigger button", () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <ImageIntelligenceView
          fileId="test-img-uuid-5678"
          filename="sample_architecture.png"
          format="png"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("sample_architecture.png")).toBeInTheDocument();
    expect(screen.getByText("png")).toBeInTheDocument();
    expect(screen.getByText("Analyze Visual Intelligence")).toBeInTheDocument();
  });
});
