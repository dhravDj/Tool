import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../src/context/ToastContext";
import { ConvertPage } from "../src/pages/ConvertPage";
import { ConversionHistoryPage } from "../src/pages/ConversionHistoryPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>{component}</BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
};

describe("Universal File Converter Pages", () => {
  it("renders ConvertPage with upload area, mode cards, and target format selectors", () => {
    renderWithProviders(<ConvertPage />);

    expect(screen.getByText("Universal File Converter & Extractor")).toBeInTheDocument();
    expect(screen.getByText("1. Select Source File")).toBeInTheDocument();
    expect(screen.getByText("2. Select Extraction Mode")).toBeInTheDocument();
    expect(screen.getByText("Mode A: Plain Text (.txt)")).toBeInTheDocument();
    expect(screen.getByText("Mode B: Structured Text (.md)")).toBeInTheDocument();
    expect(screen.getByText("Mode C: Complete Extraction (.zip)")).toBeInTheDocument();
    expect(screen.getByText("3. Target Output Format")).toBeInTheDocument();
    expect(screen.getByText("Convert & Extract Content")).toBeInTheDocument();
  });

  it("renders ConversionHistoryPage with table headers and filter controls", () => {
    renderWithProviders(<ConversionHistoryPage />);

    expect(screen.getByText("Conversion History")).toBeInTheDocument();
    expect(screen.getByText("Filter by Status:")).toBeInTheDocument();
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });
});
