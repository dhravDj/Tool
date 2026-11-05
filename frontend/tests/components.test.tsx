import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { StatCard } from "../src/components/ui/StatCard";
import { StatusIndicator } from "../src/components/ui/StatusIndicator";
import { EmptyState } from "../src/components/ui/EmptyState";
import { ConfirmDialog } from "../src/components/ui/ConfirmDialog";
import { ThemeToggle } from "../src/components/ui/ThemeToggle";

describe("Reusable UI Components", () => {
  it("renders StatCard with title, value and trend", () => {
    render(
      <StatCard
        title="Total Files"
        value={128}
        subtext="Processed in batch"
        trend="+14%"
        icon={<span data-testid="test-icon">icon</span>}
      />
    );

    expect(screen.getByText("Total Files")).toBeInTheDocument();
    expect(screen.getByText("128")).toBeInTheDocument();
    expect(screen.getByText("Processed in batch")).toBeInTheDocument();
    expect(screen.getByText("+14%")).toBeInTheDocument();
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("renders StatusIndicator with appropriate label and status dot", () => {
    const { rerender } = render(<StatusIndicator status="ok" label="HEALTHY" />);
    expect(screen.getByText("HEALTHY")).toBeInTheDocument();

    rerender(<StatusIndicator status="error" label="FAILED" />);
    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });

  it("renders EmptyState with action button", () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No Documents"
        description="No documents were found in this collection."
        action={<button onClick={onAction}>Add File</button>}
      />
    );

    expect(screen.getByText("No Documents")).toBeInTheDocument();
    expect(screen.getByText("No documents were found in this collection.")).toBeInTheDocument();

    const button = screen.getByText("Add File");
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renders ConfirmDialog and responds to confirm/cancel clicks", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    const { rerender } = render(
      <ConfirmDialog
        isOpen={false}
        title="Confirm Delete"
        description="Are you sure you want to delete this file?"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    expect(screen.queryByText("Confirm Delete")).not.toBeInTheDocument();

    rerender(
      <ConfirmDialog
        isOpen={true}
        title="Confirm Delete"
        description="Are you sure you want to delete this file?"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    expect(screen.getByText("Confirm Delete")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("renders ThemeToggle and handles toggle click", () => {
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: /toggle theme/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
  });
});
