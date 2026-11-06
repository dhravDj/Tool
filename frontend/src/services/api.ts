/** Typed HTTP client for DocuMind AI backend API. */

import {
  APIResponse,
  ArchiveAnalysisOverview,
  ArchiveCapabilities,
  ArchiveDocument,
  ArchiveEntry,
  ArchiveHierarchyNode,
  AudioCapabilities,
  AudioDocument,
  AudioEvent,
  AudioManifest,
  AudioSegment,
  BatchDetectionResponseData,
  BatchSummary,
  CanonicalDocument,
  CodeAnalysisOverview,
  CodeCapabilities,
  CodeDiagnostic,
  CodeDocument,
  CodeMetrics,
  CodeSymbol,
  DataProfile,
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
  PresentationCapabilities,
  PresentationDocument,
  PresentationManifest,
  RelationshipEdge,
  SlideData,
  SlideSummary,
  Speaker,
  SpreadsheetCapabilities,
  SpreadsheetDocument,
  SpreadsheetManifest,
  StructuredCapabilities,
  StructuredDataAnalysisOverview,
  StructuredDataDocument,
  SystemStatusData,
  AICapabilitiesResponse,
  AISettingsPayload,
  ChatRequest,
  ChatResponse,
  ComparisonRequest,
  ComparisonResponse,
  SearchQuery,
  SearchResult,
  SummaryRequest,
  SummaryResponse,
  TimelineEvent,
  VideoCapabilities,
  VideoDetection,
  VideoDocument,
  VideoKeyframe,
  VideoManifest,
  VideoScene,
  VideoTrack,
  VisionModelCapabilities,
  WorksheetData,
  WorksheetSummary,
  BatchFileItem,
  BatchProgress,
  BatchReport,
  BulkUploadManifest,
  JobAttempt,
  ProcessingBatch,
  ProcessingJob,
  ProcessingPolicy,
  QueueStatus,
  ResourceUsage,
  SystemCapacity,
  WorkerStatus,
  DashboardAnalytics,
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

  // Phase 6: Presentation Intelligence Methods
  getPresentationCapabilities: (): Promise<PresentationCapabilities> =>
    request<PresentationCapabilities>("/presentation-intelligence/capabilities"),

  analyzePresentationFile: (
    fileId: string,
    payload?: Record<string, unknown>
  ): Promise<PresentationManifest> =>
    request<PresentationManifest>(`/files/${encodeURIComponent(fileId)}/analyze-presentation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getPresentationAnalysis: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/presentation-analysis`),

  getPresentationDocumentResult: (fileId: string): Promise<PresentationDocument> =>
    request<PresentationDocument>(`/files/${encodeURIComponent(fileId)}/presentation-analysis/result`),

  getPresentationSlides: (fileId: string): Promise<SlideSummary[]> =>
    request<SlideSummary[]>(`/files/${encodeURIComponent(fileId)}/presentation-analysis/slides`),

  getSlideDetail: (fileId: string, slideId: string): Promise<SlideData> =>
    request<SlideData>(
      `/files/${encodeURIComponent(fileId)}/presentation-analysis/slides/${encodeURIComponent(slideId)}`
    ),

  getPresentationAssets: (fileId: string): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/files/${encodeURIComponent(fileId)}/presentation-analysis/assets`),

  getPresentationSummary: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/presentation-analysis/summary`),

  getPresentationDownloadUrl: (fileId: string, format = "json"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/presentation-analysis/download?format=${encodeURIComponent(
      format
    )}`,

  // Phase 7: Audio Intelligence Methods
  getAudioCapabilities: (): Promise<AudioCapabilities> =>
    request<AudioCapabilities>("/audio-intelligence/capabilities"),

  getAudioModels: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/audio-intelligence/models"),

  analyzeAudioFile: (
    fileId: string,
    payload?: Record<string, unknown>
  ): Promise<AudioManifest> =>
    request<AudioManifest>(`/files/${encodeURIComponent(fileId)}/analyze-audio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getAudioAnalysis: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/audio-analysis`),

  getAudioDocumentResult: (fileId: string): Promise<AudioDocument> =>
    request<AudioDocument>(`/files/${encodeURIComponent(fileId)}/audio-analysis/result`),

  getAudioTranscript: (
    fileId: string
  ): Promise<{ file_id: string; transcript: string; detected_language?: string; word_count: number }> =>
    request<{ file_id: string; transcript: string; detected_language?: string; word_count: number }>(
      `/files/${encodeURIComponent(fileId)}/audio-analysis/transcript`
    ),

  getAudioSegments: (fileId: string, query?: string): Promise<AudioSegment[]> => {
    const qStr = query ? `?q=${encodeURIComponent(query)}` : "";
    return request<AudioSegment[]>(`/files/${encodeURIComponent(fileId)}/audio-analysis/segments${qStr}`);
  },

  getAudioSpeakers: (fileId: string): Promise<Speaker[]> =>
    request<Speaker[]>(`/files/${encodeURIComponent(fileId)}/audio-analysis/speakers`),

  getAudioEvents: (fileId: string): Promise<AudioEvent[]> =>
    request<AudioEvent[]>(`/files/${encodeURIComponent(fileId)}/audio-analysis/events`),

  getAudioSummary: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/audio-analysis/summary`),

  getAudioExportUrl: (fileId: string, format = "srt"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/audio-analysis/export/${encodeURIComponent(format)}`,

  // Phase 8: Video Intelligence Methods
  getVideoCapabilities: (): Promise<VideoCapabilities> =>
    request<VideoCapabilities>("/video-intelligence/capabilities"),

  analyzeVideoFile: (
    fileId: string,
    payload?: Record<string, unknown>
  ): Promise<VideoManifest> =>
    request<VideoManifest>(`/files/${encodeURIComponent(fileId)}/analyze-video`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getVideoAnalysis: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/video-analysis`),

  getVideoDocumentResult: (fileId: string): Promise<VideoDocument> =>
    request<VideoDocument>(`/files/${encodeURIComponent(fileId)}/video-analysis/result`),

  getVideoSummary: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/video-analysis/summary`),

  getVideoScenes: (fileId: string): Promise<VideoScene[]> =>
    request<VideoScene[]>(`/files/${encodeURIComponent(fileId)}/video-analysis/scenes`),

  getVideoKeyframes: (fileId: string): Promise<VideoKeyframe[]> =>
    request<VideoKeyframe[]>(`/files/${encodeURIComponent(fileId)}/video-analysis/keyframes`),

  getVideoTimeline: (fileId: string): Promise<TimelineEvent[]> =>
    request<TimelineEvent[]>(`/files/${encodeURIComponent(fileId)}/video-analysis/timeline`),

  getVideoTranscript: (
    fileId: string
  ): Promise<{ file_id: string; transcript: string; speakers: Speaker[]; segments: AudioSegment[]; word_count: number }> =>
    request<{ file_id: string; transcript: string; speakers: Speaker[]; segments: AudioSegment[]; word_count: number }>(
      `/files/${encodeURIComponent(fileId)}/video-analysis/transcript`
    ),

  getVideoDetections: (fileId: string): Promise<VideoDetection[]> =>
    request<VideoDetection[]>(`/files/${encodeURIComponent(fileId)}/video-analysis/detections`),

  getVideoTracks: (fileId: string): Promise<VideoTrack[]> =>
    request<VideoTrack[]>(`/files/${encodeURIComponent(fileId)}/video-analysis/tracks`),

  getVideoExportUrl: (fileId: string, format = "srt"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/video-analysis/export/${encodeURIComponent(format)}`,

  // Phase 9: Code Intelligence Methods
  getCodeCapabilities: (): Promise<CodeCapabilities> =>
    request<CodeCapabilities>("/code-intelligence/capabilities"),

  analyzeCodeFile: (
    fileId: string,
    payload?: Record<string, unknown>
  ): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/analyze-code`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getCodeAnalysis: (fileId: string): Promise<CodeAnalysisOverview> =>
    request<CodeAnalysisOverview>(`/files/${encodeURIComponent(fileId)}/code-analysis`),

  getCodeDocumentResult: (fileId: string): Promise<CodeDocument> =>
    request<CodeDocument>(`/files/${encodeURIComponent(fileId)}/code-analysis/result`),

  getCodeSymbols: (fileId: string): Promise<CodeSymbol[]> =>
    request<CodeSymbol[]>(`/files/${encodeURIComponent(fileId)}/code-analysis/symbols`),

  getCodeDependencies: (
    fileId: string
  ): Promise<{ imports: unknown[]; dependencies: unknown[] }> =>
    request<{ imports: unknown[]; dependencies: unknown[] }>(
      `/files/${encodeURIComponent(fileId)}/code-analysis/dependencies`
    ),

  getCodeDiagnostics: (fileId: string): Promise<CodeDiagnostic[]> =>
    request<CodeDiagnostic[]>(`/files/${encodeURIComponent(fileId)}/code-analysis/diagnostics`),

  getCodeMetrics: (fileId: string): Promise<CodeMetrics> =>
    request<CodeMetrics>(`/files/${encodeURIComponent(fileId)}/code-analysis/metrics`),

  getCodeSource: (fileId: string): Promise<string> =>
    fetch(`${API_BASE}/files/${encodeURIComponent(fileId)}/code-analysis/source`).then(r => r.text()),

  getCodeExportUrl: (fileId: string, format = "json"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/code-analysis/export/${encodeURIComponent(format)}`,

  // Phase 9: Structured Data Intelligence Methods
  getStructuredCapabilities: (): Promise<StructuredCapabilities> =>
    request<StructuredCapabilities>("/structured-data-intelligence/capabilities"),

  analyzeStructuredDataFile: (
    fileId: string,
    payload?: Record<string, unknown>
  ): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/analyze-structured-data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getStructuredDataAnalysis: (fileId: string): Promise<StructuredDataAnalysisOverview> =>
    request<StructuredDataAnalysisOverview>(`/files/${encodeURIComponent(fileId)}/structured-data-analysis`),

  getStructuredDataDocumentResult: (fileId: string): Promise<StructuredDataDocument> =>
    request<StructuredDataDocument>(`/files/${encodeURIComponent(fileId)}/structured-data-analysis/result`),

  getStructuredDataSchema: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/structured-data-analysis/schema`),

  getStructuredDataProfile: (fileId: string): Promise<DataProfile> =>
    request<DataProfile>(`/files/${encodeURIComponent(fileId)}/structured-data-analysis/profile`),

  getStructuredDataRelationships: (fileId: string): Promise<RelationshipEdge[]> =>
    request<RelationshipEdge[]>(`/files/${encodeURIComponent(fileId)}/structured-data-analysis/relationships`),

  getStructuredDataRecords: (fileId: string): Promise<{ records: Record<string, unknown>[]; total_records: number }> =>
    request<{ records: Record<string, unknown>[]; total_records: number }>(
      `/files/${encodeURIComponent(fileId)}/structured-data-analysis/records`
    ),

  getStructuredDataExportUrl: (fileId: string, format = "json"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/structured-data-analysis/export/${encodeURIComponent(format)}`,

  // Phase 10: Archive Intelligence Methods
  getArchiveCapabilities: (): Promise<ArchiveCapabilities> =>
    request<ArchiveCapabilities>("/archive-intelligence/capabilities"),

  analyzeArchiveFile: (
    fileId: string,
    payload?: { mode?: string; selected_entry_ids?: string[]; password?: string }
  ): Promise<ArchiveDocument> =>
    request<ArchiveDocument>(`/files/${encodeURIComponent(fileId)}/analyze-archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  getArchiveAnalysis: (fileId: string): Promise<ArchiveAnalysisOverview> =>
    request<ArchiveAnalysisOverview>(`/files/${encodeURIComponent(fileId)}/archive-analysis`),

  getArchiveDocumentResult: (fileId: string): Promise<ArchiveDocument> =>
    request<ArchiveDocument>(`/files/${encodeURIComponent(fileId)}/archive-analysis/result`),

  getArchiveSummary: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/archive-analysis/summary`),

  getArchiveEntries: (
    fileId: string,
    params?: { skip?: number; limit?: number; entry_type?: string; search?: string }
  ): Promise<ArchiveEntry[]> => {
    const q = new URLSearchParams();
    if (params?.skip !== undefined) q.set("skip", String(params.skip));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    if (params?.entry_type) q.set("entry_type", params.entry_type);
    if (params?.search) q.set("search", params.search);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<ArchiveEntry[]>(`/files/${encodeURIComponent(fileId)}/archive-analysis/entries${qs}`);
  },

  getArchiveEntryById: (fileId: string, entryId: string): Promise<ArchiveEntry> =>
    request<ArchiveEntry>(
      `/files/${encodeURIComponent(fileId)}/archive-analysis/entries/${encodeURIComponent(entryId)}`
    ),

  getArchiveTree: (fileId: string): Promise<ArchiveHierarchyNode> =>
    request<ArchiveHierarchyNode>(`/files/${encodeURIComponent(fileId)}/archive-analysis/tree`),

  getNestedArchives: (fileId: string): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/files/${encodeURIComponent(fileId)}/archive-analysis/nested-archives`),

  extractArchiveEntries: (
    fileId: string,
    payload?: { mode?: string; password?: string }
  ): Promise<ArchiveDocument> =>
    request<ArchiveDocument>(`/files/${encodeURIComponent(fileId)}/archive-analysis/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }),

  analyzeSelectedArchiveEntries: (
    fileId: string,
    payload: { entry_ids: string[]; password?: string }
  ): Promise<ArchiveDocument> =>
    request<ArchiveDocument>(`/files/${encodeURIComponent(fileId)}/archive-analysis/analyze-selected`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getArchiveExtractionStatus: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/archive-analysis/extraction-status`),

  getArchiveChildren: (fileId: string): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/files/${encodeURIComponent(fileId)}/archive-analysis/children`),

  getArchiveSecurityReport: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/files/${encodeURIComponent(fileId)}/archive-analysis/security-report`),

  getArchiveExportUrl: (fileId: string, format = "json"): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/archive-analysis/export/${encodeURIComponent(format)}`,

  // Phase 11 — Universal AI Intelligence Endpoints
  getAICapabilities: (): Promise<AICapabilitiesResponse> =>
    request<AICapabilitiesResponse>("/ai/capabilities"),

  getAIProviders: (): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>("/ai/providers"),

  indexFileForAI: (fileId: string, force = false): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/ai/index/${encodeURIComponent(fileId)}?force=${force}`, {
      method: "POST",
    }),

  getAIIndexStatus: (fileId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/ai/index/${encodeURIComponent(fileId)}/status`),

  searchAI: (query: SearchQuery): Promise<SearchResult> =>
    request<SearchResult>("/ai/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(query),
    }),

  chatAI: (req: ChatRequest): Promise<ChatResponse> =>
    request<ChatResponse>("/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  listAIConversations: (limit = 20): Promise<Record<string, unknown>[]> =>
    request<Record<string, unknown>[]>(`/ai/conversations?limit=${limit}`),

  getAIConversation: (conversationId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/ai/conversations/${encodeURIComponent(conversationId)}`),

  deleteAIConversation: (conversationId: string): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>(`/ai/conversations/${encodeURIComponent(conversationId)}`, {
      method: "DELETE",
    }),

  summarizeFile: (req: SummaryRequest, refresh = false): Promise<SummaryResponse> =>
    request<SummaryResponse>(`/ai/summarize?refresh=${refresh}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  compareFiles: (req: ComparisonRequest): Promise<ComparisonResponse> =>
    request<ComparisonResponse>("/ai/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  extractStructuredData: (fileId: string, fields?: string[]): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/ai/extract-structured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: fileId, fields }),
    }),

  getAISettings: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/ai/settings"),

  updateAISettings: (payload: AISettingsPayload): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/ai/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getAITelemetry: (): Promise<Record<string, unknown>> =>
    request<Record<string, unknown>>("/ai/usage"),

  // Phase 12: Bulk Processing & Scalability Engine
  uploadBulkFiles: async (
    files: File[],
    batchName?: string,
    autoCreateBatch = true,
    autoStartBatch = false,
    ownerId?: string
  ): Promise<BulkUploadManifest> => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    if (batchName) formData.append("batch_name", batchName);
    formData.append("auto_create_batch", String(autoCreateBatch));
    formData.append("auto_start_batch", String(autoStartBatch));
    if (ownerId) formData.append("owner_id", ownerId);

    const response = await fetch(`${API_BASE}/bulk/upload`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Bulk upload failed with HTTP status ${response.status}`);
    }
    const resJson = await response.json();
    return resJson.data;
  },

  createBatch: (req: { name: string; policy?: Partial<ProcessingPolicy> }): Promise<ProcessingBatch> =>
    request<ProcessingBatch>("/bulk/batches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  listBatches: (params?: { limit?: number; offset?: number; status?: string; owner_id?: string }): Promise<ProcessingBatch[]> => {
    const q = new URLSearchParams();
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    if (params?.offset !== undefined) q.set("offset", String(params.offset));
    if (params?.status) q.set("status", params.status);
    if (params?.owner_id) q.set("owner_id", params.owner_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<ProcessingBatch[]>(`/bulk/batches${qs}`);
  },

  getBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}`),

  listBatchFiles: (
    batchId: string,
    params?: { limit?: number; offset?: number; status?: string }
  ): Promise<BatchFileItem[]> => {
    const q = new URLSearchParams();
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    if (params?.offset !== undefined) q.set("offset", String(params.offset));
    if (params?.status) q.set("status", params.status);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<BatchFileItem[]>(`/bulk/batches/${encodeURIComponent(batchId)}/files${qs}`);
  },

  startBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}/start`, {
      method: "POST",
    }),

  pauseBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}/pause`, {
      method: "POST",
    }),

  resumeBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}/resume`, {
      method: "POST",
    }),

  cancelBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}/cancel`, {
      method: "POST",
    }),

  retryFailedBatch: (batchId: string): Promise<ProcessingBatch> =>
    request<ProcessingBatch>(`/bulk/batches/${encodeURIComponent(batchId)}/retry-failed`, {
      method: "POST",
    }),

  getBatchProgress: (batchId: string): Promise<BatchProgress> =>
    request<BatchProgress>(`/bulk/batches/${encodeURIComponent(batchId)}/progress`),

  getBatchReport: (batchId: string): Promise<BatchReport> =>
    request<BatchReport>(`/bulk/batches/${encodeURIComponent(batchId)}/report`),

  listJobs: (params?: {
    batch_id?: string;
    status?: string;
    stage?: string;
    priority?: number;
    limit?: number;
    offset?: number;
  }): Promise<ProcessingJob[]> => {
    const q = new URLSearchParams();
    if (params?.batch_id) q.set("batch_id", params.batch_id);
    if (params?.status) q.set("status", params.status);
    if (params?.stage) q.set("stage", params.stage);
    if (params?.priority !== undefined) q.set("priority", String(params.priority));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    if (params?.offset !== undefined) q.set("offset", String(params.offset));
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<ProcessingJob[]>(`/jobs${qs}`);
  },

  getJob: (jobId: string): Promise<ProcessingJob> =>
    request<ProcessingJob>(`/jobs/${encodeURIComponent(jobId)}`),

  cancelJob: (jobId: string): Promise<ProcessingJob> =>
    request<ProcessingJob>(`/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: "POST",
    }),

  retryJob: (jobId: string): Promise<ProcessingJob> =>
    request<ProcessingJob>(`/jobs/${encodeURIComponent(jobId)}/retry`, {
      method: "POST",
    }),

  getJobAttempts: (jobId: string): Promise<JobAttempt[]> =>
    request<JobAttempt[]>(`/jobs/${encodeURIComponent(jobId)}/attempts`),

  getQueueStatus: (): Promise<QueueStatus> =>
    request<QueueStatus>("/jobs/queue/status"),

  getSystemCapacity: (): Promise<SystemCapacity> =>
    request<SystemCapacity>("/system/processing-capacity"),

  getWorkerStatus: (): Promise<WorkerStatus[]> =>
    request<WorkerStatus[]>("/system/worker-status"),

  getResourceUsage: (): Promise<ResourceUsage> =>
    request<ResourceUsage>("/system/resource-usage"),

  getDashboardAnalytics: (): Promise<DashboardAnalytics> =>
    request<DashboardAnalytics>("/system/dashboard-analytics"),

  deleteFile: (fileId: string): Promise<{ id: string; deleted: boolean }> =>
    request<{ id: string; deleted: boolean }>(`/files/${encodeURIComponent(fileId)}`, {
      method: "DELETE",
    }),

  getFileDownloadUrl: (fileId: string): string =>
    `${API_BASE}/files/${encodeURIComponent(fileId)}/download`,

  inspectDeduplication: (req: {
    filename: string;
    sha256: string;
    file_size: number;
    owner_id?: string;
  }): Promise<{
    is_duplicate: boolean;
    existing_file_id?: string;
    action: string;
    dedup_decision: string;
    existing_filename?: string;
  }> =>
    request("/bulk/inspect-deduplication", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  getJobs: (params?: {
    batch_id?: string;
    status?: string;
    stage?: string;
    priority?: number;
    limit?: number;
    offset?: number;
  }): Promise<ProcessingJob[]> => api.listJobs(params),

  indexFile: (fileId: string, options?: { force?: boolean }): Promise<Record<string, unknown>> =>
    api.indexFileForAI(fileId, options?.force ?? false),

  getIndexStatus: (fileId: string): Promise<Record<string, unknown>> =>
    api.getAIIndexStatus(fileId),
};
