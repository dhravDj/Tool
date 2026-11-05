/** Typed HTTP client for DocuMind AI backend API. */

import {
  APIResponse,
  BatchDetectionResponseData,
  BatchSummary,
  CanonicalDocument,
  DetectionCapabilitiesData,
  DetectionResultData,
  ExtractionCapabilitiesResponse,
  ExtractionManifest,
  ExtractionRequest,
  ExtractionStatusResponse,
  FileRecordSummary,
  FormatDetailData,
  FormatListResponseData,
  HealthCheckResponse,
  PluginListResponse,
  SystemStatusData,
} from "@/types/api";

const API_BASE = "/api/v1";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  const payload: APIResponse<T> = await response.json();

  if (!response.ok || !payload.success) {
    const errorMsg = payload.error?.message || `HTTP request failed: ${response.statusText}`;
    throw new Error(errorMsg);
  }

  return payload.data as T;
}

export const api = {
  getHealth: () => request<HealthCheckResponse>("/health"),
  getSystemStatus: () => request<SystemStatusData>("/system/status"),
  getPlugins: (pluginType?: string) => {
    const query = pluginType ? `?plugin_type=${encodeURIComponent(pluginType)}` : "";
    return request<PluginListResponse>(`/plugins${query}`);
  },
  getFiles: (limit = 20, offset = 0) =>
    request<FileRecordSummary[]>(`/files?limit=${limit}&offset=${offset}`),
  getBatches: (limit = 20, offset = 0) =>
    request<BatchSummary[]>(`/batches?limit=${limit}&offset=${offset}`),

  // Phase 2 Detection Endpoints
  detectFile: async (file: File, persist = true): Promise<DetectionResultData> => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DetectionResultData>(`/files/detect?persist=${persist}`, {
      method: "POST",
      body: formData,
    });
  },

  detectBatch: async (files: File[], persist = true): Promise<BatchDetectionResponseData> => {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    return request<BatchDetectionResponseData>(`/files/detect/batch?persist=${persist}`, {
      method: "POST",
      body: formData,
    });
  },

  getFileDetection: (fileId: string): Promise<DetectionResultData> =>
    request<DetectionResultData>(`/files/${encodeURIComponent(fileId)}/detection`),

  getFormats: (category?: string): Promise<FormatListResponseData> => {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    return request<FormatListResponseData>(`/formats${query}`);
  },

  getFormatById: (formatId: string): Promise<FormatDetailData> =>
    request<FormatDetailData>(`/formats/${encodeURIComponent(formatId)}`),

  getDetectionCapabilities: (): Promise<DetectionCapabilitiesData> =>
    request<DetectionCapabilitiesData>("/system/detection-capabilities"),

  // Phase 3: Document Content Extraction Endpoints
  extractDocument: (fileId: string, payload?: ExtractionRequest): Promise<ExtractionManifest> =>
    request<ExtractionManifest>(`/files/${encodeURIComponent(fileId)}/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getExtractionStatus: (fileId: string): Promise<ExtractionStatusResponse> =>
    request<ExtractionStatusResponse>(`/files/${encodeURIComponent(fileId)}/extraction`),

  getCanonicalDocument: (fileId: string): Promise<CanonicalDocument> =>
    request<CanonicalDocument>(`/files/${encodeURIComponent(fileId)}/extraction/result`),

  getExtractedMarkdown: async (fileId: string, raw = false): Promise<string> => {
    if (raw) {
      const response = await fetch(`${API_BASE}/files/${encodeURIComponent(fileId)}/extraction/markdown?raw=true`);
      return response.text();
    }
    const res = await request<{ file_id: string; markdown: string }>(
      `/files/${encodeURIComponent(fileId)}/extraction/markdown`
    );
    return res.markdown;
  },

  getExtractionManifest: (fileId: string): Promise<ExtractionManifest> =>
    request<ExtractionManifest>(`/files/${encodeURIComponent(fileId)}/extraction/manifest`),

  getExtractionCapabilities: (): Promise<ExtractionCapabilitiesResponse> =>
    request<ExtractionCapabilitiesResponse>("/extraction/capabilities"),
};
