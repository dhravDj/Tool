import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AudioIntelligenceView } from "../src/components/AudioIntelligenceView";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("AudioIntelligenceView Component", () => {
  it("renders audio intelligence overview banner and transcribe trigger button", async () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AudioIntelligenceView
          fileId="test-audio-uuid-1234"
          filename="meeting_recording.mp3"
          format="mp3"
        />
      </QueryClientProvider>
    );

    // Initial loading or loaded state
    await waitFor(() => {
      expect(screen.getByText("meeting_recording.mp3")).toBeInTheDocument();
    });

    expect(screen.getByText("mp3")).toBeInTheDocument();
    expect(screen.getByText("Transcribe & Diarize")).toBeInTheDocument();
  });
});
