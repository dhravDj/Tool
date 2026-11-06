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

// ============================================================================
// Phase 4: Image & Visual Intelligence Interfaces
// ============================================================================

export type RegionType = "text" | "object" | "diagram" | "chart" | "table" | "face" | "background";

export interface ImageMetadata {
  format: string;
  width: int_number;
  height: int_number;
  aspect_ratio: number;
  color_mode: string;
  channels: number;
  bit_depth: number;
  file_size: number;
  dpi?: [number, number] | null;
  has_transparency: boolean;
  is_animated: boolean;
  frame_count: number;
  duration_ms?: number | null;
  exif_scrubbed: Record<string, unknown>;
  gps_redacted: boolean;
}

type int_number = number;

export interface ImageRegion {
  region_id: string;
  region_type: RegionType;
  bounding_box: [number, number, number, number]; // [ymin, xmin, ymax, xmax] normalized (0.0 to 1.0)
  pixel_box?: [number, number, number, number] | null; // [x0, y0, x1, y1]
  label: string;
  text?: string | null;
  confidence: number;
  provenance: string;
  reading_order?: number | null;
  attributes: Record<string, unknown>;
}

export interface DiagramAnalysis {
  is_diagram: boolean;
  diagram_type: string;
  nodes: Array<{
    node_id: string;
    label: string;
    shape?: string;
    bounding_box?: number[];
  }>;
  connectors_count: number;
  flow_direction: string;
  confidence: number;
}

export interface ChartAnalysis {
  is_chart: boolean;
  chart_type: string;
  title?: string | null;
  x_axis_label?: string | null;
  y_axis_label?: string | null;
  legend_items: string[];
  series_data: Array<{
    label?: string;
    value?: number;
    unit?: string;
  }>;
  confidence: number;
}

export interface ImageAnalysis {
  caption: string;
  scene_type: string;
  detected_objects: string[];
  dominant_colors: string[];
  diagram: DiagramAnalysis;
  chart: ChartAnalysis;
  ocr_full_text: string;
  ocr_word_count: number;
  ocr_average_confidence: number;
}

export interface ImageDocument {
  image_id: string;
  file_id: string;
  filename: string;
  metadata: ImageMetadata;
  analysis: ImageAnalysis;
  regions: ImageRegion[];
  preprocessed_artifacts: Record<string, string>;
  warnings: string[];
  created_at: string;
}

export interface ImageManifest {
  image_id: string;
  file_id: string;
  filename: string;
  status: string;
  processing_time_seconds: number;
  engines_used: Record<string, string>;
  artifacts: Record<string, string>;
  warnings: string[];
  errors: string[];
}

export interface VisionModelCapabilities {
  supported_formats: string[];
  ocr_engine: string;
  ocr_available: boolean;
  default_vision_engine: string;
  available_vision_engines: string[];
  hardware_acceleration: string;
  max_image_dimension_px: number;
  privacy_gps_scrubbing: boolean;
  preprocessing_steps: string[];
}

export interface ImageAskRequest {
  question: string;
  focus_region_id?: string | null;
}

export interface ImageAskResponse {
  question: string;
  answer: string;
  confidence: number;
  grounding_region_ids: string[];
  reasoning?: string | null;
}

export interface ImageAnalysisStatusResponse {
  file_id: string;
  status: string;
  format: string;
  width: number;
  height: number;
  color_mode: string;
  ocr_word_count: number;
  detected_objects_count: number;
  has_charts: boolean;
  has_diagrams: boolean;
  artifacts: Record<string, string>;
  manifest?: ImageManifest | null;
}

// --------------------------------------------------------------------------
// Phase 5: Spreadsheet Intelligence Interfaces
// --------------------------------------------------------------------------

export interface CellStyle {
  font_name?: string | null;
  font_size?: number | null;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  font_color?: string | null;
  fill_color?: string | null;
  horizontal_align?: string | null;
  vertical_align?: string | null;
  number_format?: string | null;
  has_border: boolean;
}

export interface CellData {
  address: string;
  row: number;
  column: number;
  raw_value: unknown;
  formatted_value?: string | null;
  data_type: "string" | "number" | "boolean" | "date" | "time" | "datetime" | "formula" | "empty" | "error";
  formula?: string | null;
  cached_value?: unknown;
  style?: CellStyle | null;
  hyperlink?: string | null;
  comment?: string | null;
}

export interface ColumnProfiling {
  column_index: number;
  column_letter: string;
  column_name?: string | null;
  inferred_type: string;
  total_count: number;
  null_count: number;
  unique_count: number;
  min_value?: unknown;
  max_value?: unknown;
  mean?: number | null;
  median?: number | null;
  std_dev?: number | null;
  is_candidate_key: boolean;
  frequent_values: Array<{ value: string; count: number }>;
}

export interface ColumnData {
  column_index: number;
  column_letter: string;
  name?: string | null;
  width?: number | null;
  is_hidden: boolean;
  profiling?: ColumnProfiling | null;
}

export interface RowData {
  row_index: number;
  height?: number | null;
  is_hidden: boolean;
  cells: CellData[];
}

export interface TableMetadata {
  name: string;
  display_name: string;
  reference_range: string;
  columns: string[];
  has_totals_row: boolean;
}

export interface ChartMetadata {
  title?: string | null;
  chart_type: string;
  data_range?: string | null;
  series_count: number;
}

export interface WorksheetProfiling {
  total_rows: number;
  total_columns: number;
  populated_cells: number;
  empty_rows_count: number;
  duplicate_rows_count: number;
  candidate_primary_keys: string[];
  column_profiles: ColumnProfiling[];
}

export interface WorksheetData {
  sheet_id: string;
  name: string;
  position: number;
  visibility: "visible" | "hidden" | "very_hidden";
  dimensions?: string | null;
  total_rows: number;
  total_columns: number;
  merged_ranges: string[];
  columns: ColumnData[];
  rows: RowData[];
  tables: TableMetadata[];
  charts: ChartMetadata[];
  validations: unknown[];
  conditional_formats: unknown[];
  profiling?: WorksheetProfiling | null;
}

export interface WorkbookMetadata {
  filename: string;
  format: string;
  creator?: string | null;
  last_modified_by?: string | null;
  created_at?: string | null;
  modified_at?: string | null;
  sheet_count: number;
  calculation_settings: Record<string, unknown>;
  properties: Record<string, unknown>;
}

export interface SpreadsheetDocument {
  document_id: string;
  file_id: string;
  schema_version: string;
  workbook_metadata: WorkbookMetadata;
  worksheets: WorksheetData[];
  defined_names: Array<{ name: string; value: string; scope: string }>;
  relationships: Array<Record<string, unknown>>;
  assets: Array<Record<string, unknown>>;
  warnings: string[];
  extraction_metadata: Record<string, unknown>;
  created_at: string;
}

export interface SpreadsheetManifest {
  document_id: string;
  file_id: string;
  source_filename: string;
  source_format: string;
  status: string;
  engine_name: string;
  engine_version: string;
  processing_time_seconds: number;
  worksheet_count: number;
  total_rows: number;
  total_columns: number;
  total_cells: number;
  formula_count: number;
  artifacts: Record<string, string>;
  warnings: string[];
  errors: string[];
}

export interface SpreadsheetCapabilities {
  supported_formats: string[];
  max_upload_size_mb: number;
  max_rows_limit: number;
  max_columns_limit: number;
  formula_extraction_supported: boolean;
  formula_execution_allowed: boolean;
  parquet_export_available: boolean;
  supported_encodings: string[];
}

export interface WorksheetSummary {
  sheet_id: string;
  name: string;
  position: number;
  visibility: string;
  dimensions?: string | null;
  total_rows: number;
  total_columns: number;
  has_merged_cells: boolean;
  tables_count: number;
  charts_count: number;
}
