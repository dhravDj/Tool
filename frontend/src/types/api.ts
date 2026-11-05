/** API TypeScript Definitions for DocuMind AI. */

export interface APIErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  message?: string;
  error?: APIErrorDetail;
  meta?: Record<string, unknown>;
}

export interface ComponentHealth {
  status: "ok" | "degraded" | "error" | "not_configured";
  latency_ms?: number;
  message?: string;
  details?: Record<string, string>;
}

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  uptime_seconds: number;
  database: ComponentHealth;
  redis: ComponentHealth;
  storage: ComponentHealth;
  ai_engine: ComponentHealth;
}

export interface PluginMetadataSchema {
  name: string;
  version: string;
  description: string;
  author: string;
  plugin_type: "detector" | "extractor" | "ai_provider" | "storage" | "formatter";
  supported_formats: string[];
  required_dependencies: string[];
  hardware_acceleration: string;
  is_available: boolean;
  config_schema?: Record<string, unknown>;
}

export interface PluginListResponse {
  total_plugins: number;
  plugins: PluginMetadataSchema[];
}

export interface SystemStatusData {
  platform: {
    name: string;
    version: string;
    environment: string;
    os: string;
    python_version: string;
  };
  ai_engine: {
    mode: string;
    local_provider: string;
    device: string;
    cloud_processing_enabled: boolean;
    cloud_provider?: string;
  };
  storage: {
    backend: string;
    root_path: string;
    max_upload_size_mb: number;
    disk_usage: {
      total_gb: number;
      free_gb: number;
      used_gb: number;
      percent_used: number;
    };
  };
  plugins_summary: {
    total_count: number;
    active_plugins: string[];
  };
  supported_format_categories: string[];
}

export interface FileRecordSummary {
  id: string;
  original_filename: string;
  stored_filename: string;
  extension: string;
  detected_mime_type?: string;
  file_size: number;
  sha256: string;
  storage_path: string;
  status: "pending" | "stored" | "processing" | "processed" | "error" | "deleted";
  created_at: string;
  detection_format_id?: string;
  claimed_extension?: string;
  actual_extension?: string;
  format_category?: string;
  confidence_level?: "high" | "medium" | "low" | "unknown";
  confidence_score?: number;
  support_status?: string;
  is_valid?: boolean;
  is_mismatch?: boolean;
  is_corrupted?: boolean;
  is_suspicious?: boolean;
  detection_evidence?: Array<{
    signal: string;
    format_id?: string;
    mime_type?: string;
    confidence_score: number;
    details: string;
  }>;
  detection_warnings?: string[];
  file_metadata?: Record<string, unknown>;
  detection_engine_version?: string;
  detected_at?: string;
}

export interface DetectionEvidenceItem {
  signal: string;
  format_id?: string;
  mime_type?: string;
  confidence_score: number;
  details: string;
}

export interface AlternativeCandidateItem {
  format_id: string;
  canonical_name: string;
  confidence_score: number;
  reason: string;
}

export interface DetectionResultData {
  format_id: string;
  canonical_name: string;
  display_name: string;
  mime_type: string;
  extension: string;
  claimed_extension?: string;
  category: string;
  confidence_level: "high" | "medium" | "low" | "unknown";
  confidence_score: number;
  support_status: string;
  is_valid: boolean;
  is_mismatch: boolean;
  is_corrupted: boolean;
  is_suspicious: boolean;
  is_container: boolean;
  container_type?: string;
  evidence: DetectionEvidenceItem[];
  warnings: string[];
  alternative_candidates: AlternativeCandidateItem[];
  metadata: Record<string, unknown>;
  file_size: number;
  sha256: string;
  detection_duration_ms: number;
  persisted_file_id?: string;
}

export interface BatchDetectionResponseData {
  total_files: number;
  successful_detections: number;
  mismatched_extensions: number;
  suspicious_files: number;
  results: DetectionResultData[];
}

export interface FormatDetailData {
  format_id: string;
  canonical_name: string;
  display_name: string;
  category: string;
  mime_types: string[];
  extensions: string[];
  is_container: boolean;
  container_type?: string;
  support_status: string;
  extraction_plugin_id?: string;
  version_info?: string;
  description: string;
}

export interface FormatListResponseData {
  total_formats: number;
  formats: FormatDetailData[];
}

export interface DetectionCapabilitiesData {
  engine_version: string;
  libmagic_active: boolean;
  total_registered_formats: number;
  categories_count: number;
  formats_per_category: Record<string, number>;
  detection_pipeline_layers: Array<{
    step: number;
    name: string;
    description: string;
  }>;
  limits: {
    max_file_size_bytes: number;
    max_archive_entries_scanned: number;
    max_archive_decompressed_bytes: number;
    max_magic_read_bytes: number;
  };
}

export interface BatchSummary {
  id: string;
  name: string;
  total_files: number;
  queued_files: number;
  processing_files: number;
  completed_files: number;
  failed_files: number;
  cancelled_files: number;
  status: "pending" | "queued" | "processing" | "completed" | "partial_failure" | "failed" | "cancelled";
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------
// Phase 3: Document Content Extraction Schemas
// ----------------------------------------------------------------------

export type BlockType =
  | "heading"
  | "paragraph"
  | "list"
  | "list_item"
  | "table"
  | "table_row"
  | "table_cell"
  | "code"
  | "equation"
  | "caption"
  | "header"
  | "footer"
  | "image_reference"
  | "unknown";

export type ExtractionStatus =
  | "queued"
  | "processing"
  | "completed"
  | "completed_with_warnings"
  | "failed"
  | "unsupported"
  | "password_required"
  | "cancelled";

export interface CanonicalBlock {
  block_id: string;
  block_type: BlockType;
  text: string;
  reading_order: number;
  page_number: number;
  bounding_box?: [number, number, number, number] | null;
  confidence?: number | null;
  extraction_engine: string;
  provenance: string;
  warnings?: string[];
  metadata?: Record<string, unknown>;
}

export interface CanonicalPage {
  page_number: number;
  width?: number | null;
  height?: number | null;
  rotation?: number;
  is_scanned: boolean;
  ocr_applied: boolean;
  blocks: CanonicalBlock[];
  metadata?: Record<string, unknown>;
}

export interface CanonicalDocument {
  document_id: string;
  original_filename: string;
  detected_format: string;
  extraction_status: ExtractionStatus;
  metadata: Record<string, unknown>;
  page_count: number;
  extraction_engine: string;
  extraction_version: string;
  created_at: string;
  pages: CanonicalPage[];
  blocks: CanonicalBlock[];
  warnings: string[];
  errors: string[];
}

export interface ExtractionManifest {
  document_id: string;
  original_filename: string;
  detected_format: string;
  extraction_engine: string;
  extraction_version: string;
  processing_timestamp: string;
  execution_time_seconds: number;
  page_count: number;
  extracted_block_count: number;
  scanned_page_count: number;
  ocr_page_count: number;
  ocr_engine?: string | null;
  overall_confidence: number;
  warnings: string[];
  errors: string[];
  output_files: Record<string, string>;
  assets: Array<Record<string, unknown>>;
}

export interface ExtractionStatusResponse {
  file_id: string;
  status: string;
  engine: string;
  detected_format: string;
  page_count: number;
  block_count: number;
  scanned_pages: number;
  ocr_applied_pages: number;
  warnings: string[];
  errors: string[];
  output_files: Record<string, string>;
  created_at: string;
}

export interface ExtractionCapabilitiesResponse {
  supported_formats: string[];
  engines: string[];
  ocr_enabled: boolean;
  ocr_engine: string | null;
  ocr_available: boolean;
}

export interface ExtractionRequest {
  password?: string;
  extract_images?: boolean;
  options?: Record<string, unknown>;
}
