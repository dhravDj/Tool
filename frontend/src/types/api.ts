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

// ---------------------------------------------------------------------------
// Phase 6: Presentation Intelligence Types
// ---------------------------------------------------------------------------

export interface ElementPosition {
  left: number;
  top: number;
}

export interface ElementDimensions {
  width: number;
  height: number;
}

export interface SlideTextRun {
  text: string;
  font_name?: string | null;
  font_size?: number | null;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  color?: string | null;
}

export interface SlideParagraph {
  text: string;
  level: number;
  bullet: boolean;
  alignment?: string | null;
  runs: SlideTextRun[];
}

export interface SlideTableCell {
  row: number;
  column: number;
  text: string;
  is_header: boolean;
  formatting?: Record<string, unknown>;
}

export interface SlideTable {
  table_id: string;
  slide_id: string;
  slide_number: number;
  rows_count: number;
  columns_count: number;
  headers: string[];
  rows: SlideTableCell[][];
  has_header: boolean;
}

export interface SlideChartSeries {
  name: string;
  values: (number | null)[];
}

export interface SlideChart {
  chart_id: string;
  slide_id: string;
  slide_number: number;
  chart_type: string;
  title?: string | null;
  axis_titles?: Record<string, string>;
  categories: string[];
  series: SlideChartSeries[];
  legends: string[];
  data_labels: string[];
  position?: ElementPosition | null;
  dimensions?: ElementDimensions | null;
  is_inferred: boolean;
  confidence: number;
}

export interface SlideAsset {
  asset_id: string;
  slide_id: string;
  slide_number: number;
  original_filename?: string | null;
  format: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  width?: number | null;
  height?: number | null;
  position?: ElementPosition | null;
  dimensions?: ElementDimensions | null;
  alt_text?: string | null;
  storage_path?: string | null;
}

export interface DiagramNode {
  node_id: string;
  label: string;
  shape_type: string;
  position?: ElementPosition | null;
  dimensions?: ElementDimensions | null;
}

export interface DiagramEdge {
  edge_id: string;
  source_id: string;
  target_id: string;
  label?: string | null;
  arrow_type?: string | null;
}

export interface SlideDiagram {
  diagram_id: string;
  slide_id: string;
  slide_number: number;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  groups: Record<string, unknown>[];
}

export interface PresentationElement {
  element_id: string;
  element_type: "title" | "text" | "table" | "chart" | "image" | "shape" | "connector" | "group" | "unknown";
  text?: string | null;
  paragraphs: SlideParagraph[];
  position: ElementPosition;
  dimensions: ElementDimensions;
  rotation?: number;
  relationships?: Record<string, unknown>[];
  asset_reference?: string | null;
  source_provenance?: Record<string, unknown>;
  confidence?: number;
  raw_data?: Record<string, unknown> | null;
}

export interface SlideData {
  slide_id: string;
  slide_number: number;
  title?: string | null;
  layout?: string | null;
  dimensions?: ElementDimensions | null;
  elements: PresentationElement[];
  speaker_notes?: string | null;
  hidden: boolean;
  reading_order: string[];
}

export interface PresentationDimensions {
  width: number;
  height: number;
  aspect_ratio: string;
  unit: string;
}

export interface PresentationMetadata {
  title?: string | null;
  subject?: string | null;
  author?: string | null;
  created_at?: string | null;
  modified_at?: string | null;
  language?: string | null;
  slide_count: number;
  hidden_slide_count: number;
  presentation_dimensions: PresentationDimensions;
  theme?: string | null;
  layout_names: string[];
  embedded_media_count: number;
  properties?: Record<string, unknown>;
}

export interface SpeakerNoteSummary {
  slide_id: string;
  slide_number: number;
  text: string;
  word_count: number;
}

export interface PresentationDocument {
  document_id: string;
  file_id: string;
  format: string;
  metadata: PresentationMetadata;
  presentation_dimensions: PresentationDimensions;
  slide_count: number;
  slides: SlideData[];
  assets: SlideAsset[];
  charts: SlideChart[];
  tables: SlideTable[];
  diagrams: SlideDiagram[];
  speaker_notes: SpeakerNoteSummary[];
  extraction_metadata: Record<string, unknown>;
  warnings: string[];
  confidence: number;
  processing_status: string;
  created_at: string;
}

export interface PresentationManifest {
  document_id: string;
  file_id: string;
  source_filename: string;
  source_format: string;
  status: string;
  engine_name: string;
  engine_version: string;
  processing_time_seconds: number;
  slide_count: number;
  hidden_slide_count: number;
  total_elements: number;
  asset_count: number;
  table_count: number;
  chart_count: number;
  diagram_count: number;
  artifacts: Record<string, string>;
  warnings: string[];
  errors: string[];
}

export interface PresentationCapabilities {
  supported_formats: string[];
  max_upload_size_mb: number;
  max_slides_limit: number;
  max_shapes_per_slide: number;
  native_pptx_supported: boolean;
  native_odp_supported: boolean;
  legacy_ppt_supported: boolean;
  chart_extraction_supported: boolean;
  diagram_extraction_supported: boolean;
  speaker_notes_supported: boolean;
  image_intelligence_integration: boolean;
}

export interface SlideSummary {
  slide_id: string;
  slide_number: number;
  title?: string | null;
  elements_count: number;
  has_notes: boolean;
  hidden: boolean;
  reading_order: string[];
}

// Phase 7: Audio Intelligence Types
export interface AudioMetadata {
  format: string;
  codec: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  channel_layout: string;
  bit_depth?: number | null;
  bitrate_kbps?: number | null;
  file_size_bytes: number;
  audio_stream_count: number;
  title?: string | null;
  artist?: string | null;
  album?: string | null;
  genre?: string | null;
  date?: string | null;
  raw_tags: Record<string, unknown>;
}

export interface AudioWord {
  word_id: string;
  text: string;
  start: number;
  end: number;
  confidence?: number | null;
}

export interface AudioSegment {
  segment_id: string;
  start: number;
  end: number;
  text: string;
  speaker_id?: string | null;
  words: AudioWord[];
  confidence: number;
  source_chunk_id?: string | null;
}

export interface Speaker {
  speaker_id: string;
  label: string;
  segment_ids: string[];
  total_speaking_time_seconds: number;
  metadata: Record<string, unknown>;
}

export interface AudioEvent {
  event_id: string;
  category: string;
  start: number;
  end: number;
  confidence: number;
  detection_model: string;
}

export interface AudioModelInfo {
  engine_name: string;
  model_name: string;
  device: string;
  quantization?: string | null;
  is_heuristic: boolean;
}

export interface AudioDocument {
  document_id: string;
  source_file_id: string;
  format: string;
  metadata: AudioMetadata;
  duration: number;
  sample_rate: number;
  channels: number;
  codec: string;
  language?: string | null;
  language_confidence?: number | null;
  transcript: string;
  segments: AudioSegment[];
  speakers: Speaker[];
  events: AudioEvent[];
  processing_metadata: Record<string, unknown>;
  model_information: AudioModelInfo;
  warnings: string[];
  confidence: number;
  processing_status: string;
  created_at: string;
}

export interface AudioManifest {
  document_id: string;
  file_id: string;
  source_filename: string;
  source_format: string;
  status: string;
  engine_name: string;
  model_name: string;
  processing_time_seconds: number;
  duration_seconds: number;
  detected_language?: string | null;
  segment_count: number;
  word_count: number;
  speaker_count: number;
  event_count: number;
  artifacts: Record<string, string>;
  warnings: string[];
  errors: string[];
  created_at: string;
}

export interface AudioCapabilities {
  supported_formats: string[];
  max_duration_seconds: number;
  max_file_size_bytes: number;
  installed_engines: string[];
  active_engine: string;
  diarization_available: boolean;
  sound_events_available: boolean;
  hardware: Record<string, unknown>;
}

// Phase 8: Video Intelligence Types
export interface VideoStreamInfo {
  index: number;
  codec: string;
  codec_profile: string;
  width: number;
  height: number;
  resolution: string;
  fps: number;
  avg_fps: number;
  pixel_format: string;
  bit_depth?: number | null;
  color_space?: string | null;
  aspect_ratio?: string | null;
  rotation: number;
  frame_count?: number | null;
  bitrate_kbps?: number | null;
  is_variable_frame_rate: boolean;
}

export interface AudioStreamInfo {
  index: number;
  codec: string;
  codec_profile: string;
  sample_rate: number;
  channels: number;
  channel_layout: string;
  bit_depth?: number | null;
  bitrate_kbps?: number | null;
  duration_seconds: number;
  start_time_offset: number;
}

export interface VideoMetadata {
  filename: string;
  container_format: string;
  file_size_bytes: number;
  duration_seconds: number;
  bitrate_kbps?: number | null;
  stream_count: number;
  creation_time?: string | null;
  tags: Record<string, unknown>;
  video_streams: VideoStreamInfo[];
  audio_streams: AudioStreamInfo[];
}

export interface VideoDetection {
  detection_id: string;
  frame_id: string;
  timestamp: number;
  object_class: string;
  bounding_box: number[]; // [ymin, xmin, ymax, xmax]
  confidence: number;
  track_id?: string | null;
}

export interface VideoObservation {
  frame_id: string;
  timestamp: number;
  bounding_box: number[];
  confidence: number;
}

export interface VideoTrack {
  track_id: string;
  object_class: string;
  first_seen_seconds: number;
  last_seen_seconds: number;
  duration_seconds: number;
  confidence: number;
  observations: VideoObservation[];
  metadata: Record<string, unknown>;
}

export interface VideoOCRResult {
  ocr_id: string;
  text: string;
  bounding_box: number[];
  confidence: number;
  engine: string;
}

export interface VideoFrame {
  frame_id: string;
  timestamp: number;
  frame_index: number;
  asset_reference: string;
  thumbnail_reference?: string | null;
  width: number;
  height: number;
  content_hash: string;
  ocr_results: VideoOCRResult[];
  detections: VideoDetection[];
  description: string;
  scene_type: string;
  dominant_colors: string[];
}

export interface VideoKeyframe {
  keyframe_id: string;
  scene_id: string;
  frame_id: string;
  timestamp: number;
  position_type: string;
  asset_reference: string;
  thumbnail_reference: string;
  summary: string;
}

export interface VideoEvent {
  event_id: string;
  category: string;
  start: number;
  end: number;
  description: string;
  scene_id?: string | null;
  related_frame_ids: string[];
  related_track_ids: string[];
  confidence: number;
  detection_engine: string;
}

export interface VideoScene {
  scene_id: string;
  start: number;
  end: number;
  duration: number;
  start_frame: number;
  end_frame: number;
  representative_keyframe_id: string;
  frame_references: string[];
  visual_summary: string;
  transition_type: string;
  confidence: number;
  related_events: string[];
  transcript_snippets: string[];
}

export interface TimelineEvent {
  event_id: string;
  event_type: string;
  start: number;
  end: number;
  label: string;
  summary: string;
  source_reference: string;
  related_entities: string[];
}

export interface VideoModelInfo {
  engine_name: string;
  model_name: string;
  device: string;
  is_heuristic: boolean;
  ocr_engine: string;
  audio_engine?: string | null;
}

export interface VideoDocument {
  document_id: string;
  source_file_id: string;
  format: string;
  metadata: VideoMetadata;
  duration: number;
  video_streams: VideoStreamInfo[];
  audio_streams: AudioStreamInfo[];
  scenes: VideoScene[];
  keyframes: VideoKeyframe[];
  frames: VideoFrame[];
  detections: VideoDetection[];
  tracks: VideoTrack[];
  visual_events: VideoEvent[];
  transcript: string;
  speakers: Speaker[];
  transcript_segments: AudioSegment[];
  audio_events: AudioEvent[];
  timeline: TimelineEvent[];
  assets: string[];
  processing_metadata: Record<string, unknown>;
  model_information: VideoModelInfo;
  warnings: string[];
  confidence: number;
  processing_status: string;
  created_at: string;
}

export interface VideoManifest {
  document_id: string;
  file_id: string;
  source_filename: string;
  source_format: string;
  status: string;
  engine_name: string;
  model_name: string;
  processing_time_seconds: number;
  duration_seconds: number;
  scene_count: number;
  keyframe_count: number;
  detection_count: number;
  track_count: number;
  transcript_word_count: number;
  artifacts: Record<string, string>;
  warnings: string[];
  errors: string[];
  created_at: string;
}

export interface VideoCapabilities {
  supported_formats: string[];
  max_duration_seconds: number;
  max_file_size_bytes: number;
  installed_engines: string[];
  active_engine: string;
  scene_detection_available: boolean;
  ocr_available: boolean;
  tracking_available: boolean;
  audio_integration_available: boolean;
  hardware: Record<string, unknown>;
}

// --------------------------------------------------------------------------
// Phase 9: Code & Structured Data Intelligence Interfaces
// --------------------------------------------------------------------------

export interface CodeSymbol {
  symbol_id: string;
  name: string;
  symbol_type: string;
  start_line: number;
  end_line: number;
  parent_symbol?: string | null;
  visibility: string;
  parameters: string[];
  return_type?: string | null;
  documentation?: string | null;
  source_reference?: string | null;
}

export interface CodeImport {
  statement: string;
  module_name: string;
  imported_symbols: string[];
  is_relative: boolean;
  is_external: boolean;
  line_number: number;
}

export interface CodeDependency {
  name: string;
  version_constraint?: string | null;
  dependency_type: string;
  package_manager?: string | null;
  is_direct: boolean;
}

export interface CodeMetrics {
  total_lines: number;
  code_lines: number;
  comment_lines: number;
  blank_lines: number;
  function_count: number;
  class_count: number;
  import_count: number;
  comment_ratio: number;
  avg_function_length: number;
  max_function_length: number;
  cyclomatic_complexity: number;
  nesting_depth: number;
  duplicate_code_candidates: string[];
}

export interface CodeDiagnostic {
  diagnostic_id: string;
  rule_id: string;
  severity: "error" | "warning" | "info" | "hint" | string;
  message: string;
  file_path: string;
  start_line: number;
  end_line: number;
  column: number;
  tool_name: string;
  evidence?: string | null;
  suggested_remediation?: string | null;
}

export interface SyntaxValidationResult {
  is_valid: boolean;
  parser_used: string;
  errors: string[];
}

export interface CodeModelInfo {
  engine_name: string;
  parser_type: string;
  is_compiler: boolean;
  capabilities: string[];
}

export interface CodeDocument {
  document_id: string;
  source_file_id: string;
  language: string;
  encoding: string;
  file_metadata: Record<string, unknown>;
  symbols: CodeSymbol[];
  imports: CodeImport[];
  dependencies: CodeDependency[];
  metrics: CodeMetrics;
  diagnostics: CodeDiagnostic[];
  syntax_validation: SyntaxValidationResult;
  source_references: string[];
  processing_metadata: Record<string, unknown>;
  model_information: CodeModelInfo;
  warnings: string[];
  status: string;
}

export interface CodeAnalysisOverview {
  id: string;
  file_id: string;
  status: string;
  language: string;
  total_lines: number;
  code_lines: number;
  comment_lines: number;
  blank_lines: number;
  symbol_count: number;
  function_count: number;
  class_count: number;
  import_count: number;
  diagnostic_count: number;
  has_syntax_errors: boolean;
  cyclomatic_complexity: number;
  model_name: string;
  warnings: string[];
  artifacts: Record<string, string>;
  created_at: string;
}

export interface CodeCapabilities {
  supported_languages: string[];
  installed_parsers: string[];
  features: string[];
  max_file_size_bytes: number;
}

export interface ColumnStatistics {
  min_value?: unknown;
  max_value?: unknown;
  null_count: number;
  distinct_count?: number | null;
  sample_values: unknown[];
}

export interface ColumnProfile {
  name: string;
  data_type: string;
  physical_type?: string | null;
  null_percentage: number;
  is_unique: boolean;
  is_candidate_key: boolean;
  statistics?: ColumnStatistics | null;
}

export interface DataProfile {
  total_rows: number;
  total_columns: number;
  candidate_keys: string[];
  missing_cells_ratio: number;
  column_profiles: ColumnProfile[];
}

export interface StructuredValidationResult {
  is_valid: boolean;
  syntax_valid: boolean;
  duplicate_keys: string[];
  schema_errors: string[];
  security_warnings: string[];
}

export interface RelationshipEdge {
  source_entity: string;
  source_field: string;
  target_entity: string;
  target_field: string;
  relationship_type: string;
  confidence: number;
}

export interface StructuredModelInfo {
  engine_name: string;
  format_parser: string;
  is_bounded_memory: boolean;
  features_used: string[];
}

export interface StructuredDataDocument {
  document_id: string;
  source_file_id: string;
  format: string;
  root_type: string;
  schema_definition: Record<string, unknown>;
  hierarchy: unknown;
  records: Record<string, unknown>[];
  data_profile: DataProfile;
  validation_results: StructuredValidationResult;
  relationships: RelationshipEdge[];
  metadata: Record<string, unknown>;
  processing_metadata: Record<string, unknown>;
  model_information: StructuredModelInfo;
  warnings: string[];
  status: string;
  raw_preview: string;
}

export interface StructuredDataAnalysisOverview {
  id: string;
  file_id: string;
  status: string;
  format: string;
  root_type: string;
  record_count: number;
  field_count: number;
  max_depth: number;
  is_valid: boolean;
  compression: string;
  model_name: string;
  warnings: string[];
  artifacts: Record<string, string>;
  created_at: string;
}

export interface StructuredCapabilities {
  supported_formats: string[];
  installed_engines: string[];
  features: string[];
  max_file_size_bytes: number;
}



