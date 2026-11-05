import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../src/app/App";

describe("Frontend Routing and Shell Rendering", () => {
  it("renders main platform layout and navigation bar", () => {
    render(<App />);

    // Brand and platform indicators
    expect(screen.getByText("DocuMind AI")).toBeInTheDocument();
    expect(screen.getByText("Phase 1 Core")).toBeInTheDocument();

    // Nav links
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Upload & Ingest")).toBeInTheDocument();
    expect(screen.getByText("Processing Jobs")).toBeInTheDocument();
    expect(screen.getByText("File Library")).toBeInTheDocument();
    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });
});
