import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ArchiveIntelligenceView } from "../src/components/ArchiveIntelligenceView";
import { api } from "../src/services/api";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("ArchiveIntelligenceView Component", () => {
  it("renders archive intelligence overview, safety metrics, and tabs", async () => {
    const queryClient = createTestQueryClient();

    vi.spyOn(api, "getArchiveAnalysis").mockResolvedValue({
      id: "archive_analysis_123",
      file_id: "test-archive-uuid",
      status: "completed",
      archive_format: "zip",
      processing_mode: "mode_c_extract_and_analyze",
      entry_count: 5,
      file_count: 4,
      directory_count: 1,
      nested_archive_count: 0,
      total_uncompressed_size: 1048576,
      extracted_size: 1048576,
      compression_ratio: 2.0,
      is_encrypted: false,
      is_corrupted: false,
      safety_report: {
        path_traversal_blocked: 0,
        symlink_entries_blocked: 0,
        suspicious_entries: 0,
        size_limit_exceeded: false,
        compression_ratio_exceeded: false,
        entry_limit_exceeded: false,
        nesting_limit_exceeded: false,
        timeout_exceeded: false,
        encryption_detected: false,
        corruption_detected: false,
        blocked_entry_count: 0,
        warnings: [],
      },
      artifacts: {
        archive_json: "archive_123_data.json",
        markdown_summary: "archive_123_summary.md",
        manifest_csv: "archive_123_manifest.csv",
        tree_text: "archive_123_tree.txt",
        extraction_report: "archive_123_extraction.json",
        security_audit: "archive_123_security.json",
      },
      created_at: new Date().toISOString(),
    });

    vi.spyOn(api, "getArchiveDocumentResult").mockResolvedValue({
      archive_id: "archive_123",
      source_file_id: "test-archive-uuid",
      archive_format: "zip",
      metadata: {
        total_entries: 5,
        file_count: 4,
        directory_count: 1,
        total_uncompressed_size: 1048576,
        compression_ratio: 2.0,
      },
      entries: [
        {
          entry_id: "entry_1",
          original_path: "src/main.py",
          normalized_path: "src/main.py",
          filename: "main.py",
          extension: "py",
          entry_type: "file",
          compressed_size: 1024,
          uncompressed_size: 2048,
          compression_method: "deflate",
          checksum: "1234abcd",
          encrypted: false,
          is_directory: false,
          is_symlink: false,
          is_nested_archive: false,
          detection_result: { category: "code" },
          extracted_file_id: null,
          processing_status: "extracted",
          error: null,
        },
        {
          entry_id: "entry_2",
          original_path: "docs/readme.txt",
          normalized_path: "docs/readme.txt",
          filename: "readme.txt",
          extension: "txt",
          entry_type: "file",
          compressed_size: 512,
          uncompressed_size: 1024,
          compression_method: "deflate",
          checksum: "5678efab",
          encrypted: false,
          is_directory: false,
          is_symlink: false,
          is_nested_archive: false,
          detection_result: { category: "document" },
          extracted_file_id: null,
          processing_status: "extracted",
          error: null,
        },
      ],
      hierarchy: {
        id: "root",
        name: "root",
        path: "",
        is_directory: true,
        is_nested_archive: false,
        entry_id: null,
        children: [
          {
            id: "src",
            name: "src",
            path: "src",
            is_directory: true,
            is_nested_archive: false,
            entry_id: null,
            children: [
              {
                id: "main_py",
                name: "main.py",
                path: "src/main.py",
                is_directory: false,
                is_nested_archive: false,
                entry_id: "entry_1",
                children: [],
                file_count: 1,
                total_size: 2048,
                warnings: [],
              },
            ],
            file_count: 1,
            total_size: 2048,
            warnings: [],
          },
        ],
        file_count: 2,
        total_size: 3072,
        warnings: [],
      },
      nested_archives: [],
      extracted_files: [
        {
          original_path: "src/main.py",
          file_size: 2048,
          sha256: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
          downstream_engine: "Code Intelligence",
          created_file_id: "child_file_uuid_1",
        },
      ],
      blocked_entries: [],
      failed_entries: [],
      processing_mode: "mode_c_extract_and_analyze",
      processing_status: "completed",
      extracted_size: 1048576,
      total_entry_count: 5,
      nesting_depth: 1,
      safety_report: {
        path_traversal_blocked: 0,
        symlink_entries_blocked: 0,
        suspicious_entries: 0,
        size_limit_exceeded: false,
        compression_ratio_exceeded: false,
        entry_limit_exceeded: false,
        nesting_limit_exceeded: false,
        timeout_exceeded: false,
        encryption_detected: false,
        corruption_detected: false,
        blocked_entry_count: 0,
        warnings: [],
      },
      processing_metadata: {},
      warnings: [],
      errors: [],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ArchiveIntelligenceView
          fileId="test-archive-uuid"
          filename="test_bundle.zip"
        />
      </QueryClientProvider>
    );

    // Verify basic overview headers and metrics render
    await waitFor(() => {
      expect(screen.getByText("test_bundle.zip")).toBeInTheDocument();
      expect(screen.getByText("Overview")).toBeInTheDocument();
      expect(screen.getByText("Hierarchy Tree")).toBeInTheDocument();
      expect(screen.getByText("Entries Manifest")).toBeInTheDocument();
      expect(screen.getByText("Extraction Results")).toBeInTheDocument();
      expect(screen.getByText("Security Audit")).toBeInTheDocument();
      expect(screen.getByText("Downloads & Exports")).toBeInTheDocument();
    });

    // Test tab navigation to Security Audit
    const securityTab = screen.getByText("Security Audit");
    fireEvent.click(securityTab);

    await waitFor(() => {
      expect(screen.getByText("Security & Vulnerability Assessment")).toBeInTheDocument();
      expect(screen.getByText("Path Traversals Blocked")).toBeInTheDocument();
      expect(screen.getByText("Archive Bomb Flag")).toBeInTheDocument();
      expect(screen.getByText("CLEAN")).toBeInTheDocument();
    });

    // Test tab navigation to Downloads & Exports
    const downloadsTab = screen.getByText("Downloads & Exports");
    fireEvent.click(downloadsTab);

    await waitFor(() => {
      expect(screen.getByText("Download Artifacts & Reports")).toBeInTheDocument();
      expect(screen.getByText("Archive Document JSON")).toBeInTheDocument();
      expect(screen.getByText("Archive Markdown Report")).toBeInTheDocument();
      expect(screen.getByText("Directory Hierarchy Tree")).toBeInTheDocument();
    });
  });
});
