import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../src/app/App";

describe("Frontend Routing and Shell Rendering", () => {
  it("renders main platform layout and navigation bar", () => {
    render(<App />);

    // Brand and platform indicators
    expect(screen.getByText("DocuMind AI")).toBeInTheDocument();
    expect(screen.getByText("Universal SaaS")).toBeInTheDocument();

    // Nav links
    expect(screen.getAllByText("Bulk Converter").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Conversion History").length).toBeGreaterThan(0);
    expect(screen.getAllByText("System Status").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Settings").length).toBeGreaterThan(0);
  });
});
