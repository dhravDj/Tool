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
  ImageAnalysisStatusResponse,
  ImageAskResponse,
  ImageDocument,
  ImageManifest,
  PluginListResponse,
  SpreadsheetCapabilities,
  SpreadsheetDocument,
  SpreadsheetManifest,
  SystemStatusData,
  VisionModelCapabilities,
  WorksheetData,
  WorksheetSummary,
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

  // Phase 4: Image & Visual Intelligence Endpoints
  getImageIntelligenceCapabilities: (): Promise<VisionModelCapabilities> =>
    request<VisionModelCapabilities>("/image-intelligence/capabilities"),

  analyzeImage: (fileId: string, options?: Record<string, unknown>): Promise<ImageManifest> =>
    request<ImageManifest>(`/files/${encodeURIComponent(fileId)}/analyze-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(options || {}),
    }),

  getImageAnalysisStatus: (fileId: string): Promise<ImageAnalysisStatusResponse> =>
    request<ImageAnalysisStatusResponse>(`/files/${encodeURIComponent(fileId)}/image-analysis`),

  getCanonicalImageDocument: (fileId: string): Promise<ImageDocument> =>
    request<ImageDocument>(`/files/${encodeURIComponent(fileId)}/image-analysis/result`),

  askImageQuestion: (fileId: string, question: string, focusRegionId?: string): Promise<ImageAskResponse> =>
    request<ImageAskResponse>(`/files/${encodeURIComponent(fileId)}/ask-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, focus_region_id: focusRegionId }),
    }),

  // Phase 5: Spreadsheet Intelligence Endpoints
  getSpreadsheetCapabilities: (): Promise<SpreadsheetCapabilities> =>
    request<SpreadsheetCapabilities>("/spreadsheet-intelligence/capabilities"),

  analyzeSpreadsheet: (fileId: string, options?: Record<string, unknown>): Promise<SpreadsheetManifest> =>
    request<SpreadsheetManifest>(`/files/${encodeURIComponent(fileId)}/analyze-spreadsheet`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(options || {}),
    }),

  getSpreadsheetAnalysisStatus: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/spreadsheet-analysis`),

  getCanonicalSpreadsheetDocument: (fileId: string): Promise<SpreadsheetDocument> =>
    request<SpreadsheetDocument>(`/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/result`),

  getWorksheets: (fileId: string): Promise<WorksheetSummary[]> =>
    request<WorksheetSummary[]>(`/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/worksheets`),

  getWorksheetData: (
    fileId: string,
    sheetId: string,
    page = 1,
    pageSize = 50
  ): Promise<WorksheetData & { page: number; total_pages: number }> =>
    request<WorksheetData & { page: number; total_pages: number }>(
      `/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/worksheets/${encodeURIComponent(
        sheetId
      )}?page=${page}&page_size=${pageSize}`
    ),

  getSpreadsheetSummary: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/summary`),

  getSpreadsheetManifest: (fileId: string): Promise<SpreadsheetManifest> =>
    request<SpreadsheetManifest>(`/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/manifest`),

  getSpreadsheetDownloadUrl: (fileId: string, format = "json", sheetPosition = 1): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/spreadsheet-analysis/download?format=${encodeURIComponent(
      format
    )}&sheet_position=${sheetPosition}`,
};
