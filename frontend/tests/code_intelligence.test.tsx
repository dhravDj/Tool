import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CodeIntelligenceView } from "../src/components/CodeIntelligenceView";
import { api } from "../src/services/api";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("CodeIntelligenceView Component", () => {
  it("renders code intelligence view with symbols and metrics", async () => {
    const queryClient = createTestQueryClient();

    vi.spyOn(api, "getCodeDocumentResult").mockResolvedValue({
      document_id: "code_123",
      source_file_id: "test-code-uuid",
      language: "python",
      encoding: "utf-8",
      file_metadata: {},
      symbols: [
        {
          symbol_id: "sym_1",
          name: "calculateTax",
          symbol_type: "function",
          start_line: 10,
          end_line: 25,
          visibility: "public",
          parameters: ["amount", "rate"],
          return_type: "float",
        },
      ],
      imports: [
        {
          statement: "import math",
          module_name: "math",
          imported_symbols: ["math"],
          is_relative: false,
          is_external: false,
          line_number: 1,
        },
      ],
      dependencies: [
        {
          name: "numpy",
          dependency_type: "runtime",
          is_direct: true,
        },
      ],
      metrics: {
        total_lines: 45,
        code_lines: 38,
        comment_lines: 4,
        blank_lines: 3,
        function_count: 1,
        class_count: 0,
        import_count: 1,
        comment_ratio: 8.89,
        avg_function_length: 15,
        max_function_length: 15,
        cyclomatic_complexity: 2.0,
        nesting_depth: 2,
        duplicate_code_candidates: [],
      },
      diagnostics: [],
      syntax_validation: {
        is_valid: true,
        parser_used: "ast",
        errors: [],
      },
      source_references: [],
      processing_metadata: {},
      model_information: {
        engine_name: "documind-code-v1",
        parser_type: "PythonParser",
        is_compiler: false,
        capabilities: ["ast"],
      },
      warnings: [],
      status: "completed",
    });

    vi.spyOn(api, "getCodeAnalysis").mockResolvedValue({
      id: "rec_1",
      file_id: "test-code-uuid",
      status: "completed",
      language: "python",
      total_lines: 45,
      code_lines: 38,
      comment_lines: 4,
      blank_lines: 3,
      symbol_count: 1,
      function_count: 1,
      class_count: 0,
      import_count: 1,
      diagnostic_count: 0,
      has_syntax_errors: false,
      cyclomatic_complexity: 2.0,
      model_name: "documind-code-v1",
      warnings: [],
      artifacts: {},
      created_at: new Date().toISOString(),
    });

    vi.spyOn(api, "getCodeSource").mockResolvedValue("import math\n\ndef calculateTax(amount, rate):\n    return amount * rate\n");

    render(
      <QueryClientProvider client={queryClient}>
        <CodeIntelligenceView
          fileId="test-code-uuid"
          filename="calculator.py"
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("calculator.py")).toBeInTheDocument();
      expect(screen.getByText("python")).toBeInTheDocument();
      expect(screen.getByText("Lines of Code")).toBeInTheDocument();
      expect(screen.getByText("Cyclomatic Complexity")).toBeInTheDocument();
    });
  });
});
