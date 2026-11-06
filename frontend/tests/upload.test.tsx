import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../src/context/ToastContext";
import { UploadPage } from "../src/pages/UploadPage";

const queryClient = new QueryClient();

describe("UploadPage Component", () => {
  it("renders upload dropzone, security safeguards banner, and controls", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <BrowserRouter>
            <UploadPage />
          </BrowserRouter>
        </ToastProvider>
      </QueryClientProvider>
    );

    expect(
      screen.getByText("Universal Detection & Ingestion Gateway")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Zero-Trust Multi-Signal Ingestion Active")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Drag & drop files or folders to ingest/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Browse Files")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Select Directory")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Persist validated files to platform library automatically/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Ingested File Results")
    ).toBeInTheDocument();
    expect(
      screen.getByText("No files evaluated in current session")
    ).toBeInTheDocument();
  });
});
