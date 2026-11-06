import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StructuredDataIntelligenceView } from "../src/components/StructuredDataIntelligenceView";
import { api } from "../src/services/api";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("StructuredDataIntelligenceView Component", () => {
  it("renders structured data intelligence view with column profiles and rows", async () => {
    const queryClient = createTestQueryClient();

    vi.spyOn(api, "getStructuredDataDocumentResult").mockResolvedValue({
      document_id: "struct_123",
      source_file_id: "test-struct-uuid",
      format: "parquet",
      root_type: "table",
      schema_definition: { columns: ["id", "user_name", "balance"] },
      hierarchy: {},
      records: [
        { id: 1, user_name: "Alice", balance: 500.0 },
        { id: 2, user_name: "Bob", balance: 750.5 },
      ],
      data_profile: {
        total_rows: 2,
        total_columns: 3,
        candidate_keys: ["id"],
        missing_cells_ratio: 0.0,
        column_profiles: [
          {
            name: "id",
            data_type: "int64",
            null_percentage: 0.0,
            is_unique: true,
            is_candidate_key: true,
            statistics: { null_count: 0, distinct_count: 2, sample_values: [1, 2] },
          },
          {
            name: "user_name",
            data_type: "string",
            null_percentage: 0.0,
            is_unique: true,
            is_candidate_key: false,
            statistics: { null_count: 0, distinct_count: 2, sample_values: ["Alice", "Bob"] },
          },
        ],
      },
      validation_results: {
        is_valid: true,
        syntax_valid: true,
        duplicate_keys: [],
        schema_errors: [],
        security_warnings: [],
      },
      relationships: [],
      metadata: {},
      processing_metadata: {},
      model_information: {
        engine_name: "documind-structured-v1",
        format_parser: "pyarrow",
        is_bounded_memory: true,
        features_used: ["zero_dataframe"],
      },
      warnings: [],
      status: "completed",
      raw_preview: "parquet preview data",
    });

    vi.spyOn(api, "getStructuredDataAnalysis").mockResolvedValue({
      id: "rec_struct_1",
      file_id: "test-struct-uuid",
      status: "completed",
      format: "parquet",
      root_type: "table",
      record_count: 2,
      field_count: 3,
      max_depth: 1,
      is_valid: true,
      compression: "snappy",
      model_name: "documind-structured-v1",
      warnings: [],
      artifacts: {},
      created_at: new Date().toISOString(),
    });

    render(
      <QueryClientProvider client={queryClient}>
        <StructuredDataIntelligenceView
          fileId="test-struct-uuid"
          filename="users.parquet"
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("users.parquet")).toBeInTheDocument();
      expect(screen.getByText("parquet")).toBeInTheDocument();
      expect(screen.getByText("Rows / Records")).toBeInTheDocument();
      expect(screen.getByText("Candidate Keys")).toBeInTheDocument();
    });
  });
});
