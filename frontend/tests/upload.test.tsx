import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UploadPage } from "../src/pages/UploadPage";

const queryClient = new QueryClient();

describe("UploadPage Component", () => {
  it("renders upload dropzone, security safeguards banner, and controls", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <UploadPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(
      screen.getByText("Universal Detection & Ingestion Gateway")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Zero-Trust Multi-Signal Detection Active")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Drag and drop files to detect")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Browse Local Files")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Persist identified files to storage library")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Detection Results")
    ).toBeInTheDocument();
    expect(
      screen.getByText("No files evaluated yet")
    ).toBeInTheDocument();
  });
});
