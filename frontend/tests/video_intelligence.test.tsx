import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { VideoIntelligenceView } from "../src/components/VideoIntelligenceView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("VideoIntelligenceView Component", () => {
  it("renders video intelligence inspector header and analyze trigger button", () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <VideoIntelligenceView
          fileId="test-video-uuid-1234"
          filename="presentation_demo.mp4"
          format="mp4"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText("presentation_demo.mp4")).toBeInTheDocument();
    expect(screen.getByText("mp4")).toBeInTheDocument();
    expect(screen.getByText("Analyze Video Intelligence")).toBeInTheDocument();
  });
});
