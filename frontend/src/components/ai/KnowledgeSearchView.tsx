import React, { useState } from "react";
import {
  FileCode,
  FileSpreadsheet,
  FileText,
  Filter,
  Layers,
  Music,
  Package,
  Presentation,
  Search,
  SlidersHorizontal,
  Sparkles,
  Video,
  Zap,
} from "lucide-react";
import { api } from "@/services/api";
import { SearchResult } from "@/types/api";

const MODALITY_ICONS: Record<string, React.ReactNode> = {
  document: <FileText className="w-4 h-4 text-blue-500" />,
  spreadsheet: <FileSpreadsheet className="w-4 h-4 text-emerald-500" />,
  presentation: <Presentation className="w-4 h-4 text-amber-500" />,
  audio: <Music className="w-4 h-4 text-purple-500" />,
  video: <Video className="w-4 h-4 text-rose-500" />,
  code: <FileCode className="w-4 h-4 text-cyan-500" />,
  structured_data: <Layers className="w-4 h-4 text-indigo-500" />,
  archive: <Package className="w-4 h-4 text-orange-500" />,
};

export const KnowledgeSearchView: React.FC = () => {
  const [query, setQuery] = useState("");
  const [searchMode, setSearchMode] = useState<"hybrid" | "semantic" | "keyword">("hybrid");
  const [selectedModality, setSelectedModality] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const res = await api.searchAI({
        query: query.trim(),
        search_mode: searchMode,
        top_k: 12,
        filter:
          selectedModality !== "all"
            ? { source_types: [selectedModality] }
            : undefined,
      });
      setResults(res);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Header Bar */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <form onSubmit={handleSearch} className="space-y-3">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 absolute left-3.5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across all indexed files, schemas, transcripts, and code..."
              className="w-full pl-11 pr-24 py-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="absolute right-2 px-4 py-1.5 rounded-md bg-blue-600 text-white text-xs font-medium hover:bg-blue-700 disabled:opacity-50 transition-all shadow-xs"
            >
              {isLoading ? "Searching..." : "Search"}
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
            {/* Mode Selector */}
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setSearchMode("hybrid")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                  searchMode === "hybrid"
                    ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 font-medium shadow-xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                Hybrid (RRF)
              </button>
              <button
                type="button"
                onClick={() => setSearchMode("semantic")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                  searchMode === "semantic"
                    ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 font-medium shadow-xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Semantic
              </button>
              <button
                type="button"
                onClick={() => setSearchMode("keyword")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                  searchMode === "keyword"
                    ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 font-medium shadow-xs"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                BM25 Keyword
              </button>
            </div>

            {/* Modality Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedModality}
                onChange={(e) => setSelectedModality(e.target.value)}
                className="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs focus:outline-hidden"
              >
                <option value="all">All Modalities</option>
                <option value="document">Documents (PDF, Word, Text)</option>
                <option value="spreadsheet">Spreadsheets (Excel, CSV)</option>
                <option value="presentation">Presentations (PPTX)</option>
                <option value="audio">Audio (Transcripts)</option>
                <option value="video">Video (Scenes & Speech)</option>
                <option value="code">Source Code (AST Symbols)</option>
                <option value="structured_data">Structured Data (JSON, XML)</option>
                <option value="archive">Archives (ZIP, TAR)</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Results Header */}
      {results && (
        <div className="flex items-center justify-between px-1 text-xs text-slate-500 dark:text-slate-400">
          <div>
            Found <span className="font-semibold text-slate-800 dark:text-slate-200">{results.total_hits}</span> matching chunks for &ldquo;{results.query}&rdquo;
          </div>
          <div>
            Latency: <span className="font-mono text-slate-700 dark:text-slate-300">{results.duration_ms}ms</span> ({results.search_mode} mode)
          </div>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-3">
        {results?.hits.map((hit) => {
          const icon = MODALITY_ICONS[hit.source_type] || <FileText className="w-4 h-4 text-slate-400" />;
          return (
            <div
              key={hit.chunk_id}
              className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs hover:border-blue-300 dark:hover:border-blue-700 transition-all"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800">
                    {icon}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                      {hit.filename}
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 font-medium">
                        {hit.source_reference.formatted_citation}
                      </span>
                    </h4>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    Score: {(hit.score * 100).toFixed(1)}%
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                    {hit.search_method}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans whitespace-pre-wrap bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                {hit.content}
              </p>
            </div>
          );
        })}

        {results && results.hits.length === 0 && (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400 border border-dashed rounded-xl">
            No matching knowledge chunks found. Try expanding your search terms or re-indexing files.
          </div>
        )}
      </div>
    </div>
  );
};
