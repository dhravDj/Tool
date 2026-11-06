import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../src/components/ui/Button";
import { Badge } from "../src/components/ui/Badge";
import { Modal } from "../src/components/ui/Modal";

describe("Hallmark Design System UI Components", () => {
  describe("Button Component", () => {
    it("renders primary button variant with text and responds to click", () => {
      const handleClick = vi.fn();
      render(
        <Button variant="primary" onClick={handleClick}>
          Run Pipeline
        </Button>
      );

      const btn = screen.getByRole("button", { name: /Run Pipeline/i });
      expect(btn).toBeInTheDocument();
      fireEvent.click(btn);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("displays loading spinner and disables click when isLoading is true", () => {
      const handleClick = vi.fn();
      render(
        <Button variant="primary" isLoading onClick={handleClick}>
          Saving
        </Button>
      );

      const btn = screen.getByRole("button");
      expect(btn).toBeDisabled();
      fireEvent.click(btn);
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("Badge Component", () => {
    it("renders with correct variant styles and children", () => {
      render(<Badge variant="success">Completed</Badge>);
      expect(screen.getByText("Completed")).toBeInTheDocument();
    });
  });

  describe("Modal Component", () => {
    it("renders modal content when isOpen is true and calls onClose on backdrop click", () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen={true} onClose={handleClose} title="File Details">
          <p>Modal body content</p>
        </Modal>
      );

      expect(screen.getByText("File Details")).toBeInTheDocument();
      expect(screen.getByText("Modal body content")).toBeInTheDocument();

      const closeButton = screen.getByLabelText("Close dialog");
      fireEvent.click(closeButton);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it("does not render when isOpen is false", () => {
      render(
        <Modal isOpen={false} onClose={() => {}} title="Hidden Dialog">
          <p>Hidden body</p>
        </Modal>
      );

      expect(screen.queryByText("Hidden Dialog")).not.toBeInTheDocument();
    });
  });
});
