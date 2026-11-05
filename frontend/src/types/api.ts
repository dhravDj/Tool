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
