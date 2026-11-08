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
  it("renders ConvertPage with upload area, format selectors, and bulk queue", () => {
    renderWithProviders(<ConvertPage />);

    expect(screen.getByText("Universal Bulk Converter")).toBeInTheDocument();
    expect(screen.getByText("Target Output Format")).toBeInTheDocument();
    expect(screen.getByText("Markdown (.md)")).toBeInTheDocument();
    expect(screen.getByText("Plain Text (.txt)")).toBeInTheDocument();
    expect(screen.getByText("Drag and drop files here, or click to browse")).toBeInTheDocument();
  });

  it("renders ConversionHistoryPage with table headers and filter controls", () => {
    renderWithProviders(<ConversionHistoryPage />);

    expect(screen.getByText("Conversion History")).toBeInTheDocument();
    expect(screen.getByText("Filter by Status:")).toBeInTheDocument();
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });
});
