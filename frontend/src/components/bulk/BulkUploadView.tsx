import React, { useState, useRef } from "react";
import { api } from "../../services/api";
import { BulkUploadManifest } from "../../types/api";

interface BulkUploadViewProps {
  onBatchCreated?: (batchId: string) => void;
}

export const BulkUploadView: React.FC<BulkUploadViewProps> = ({ onBatchCreated }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [batchName, setBatchName] = useState<string>("");
  const [priority, setPriority] = useState<number>(30); // Default Bulk
  const [autoStart, setAutoStart] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [manifest, setManifest] = useState<BulkUploadManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dirInputRef = useRef<HTMLInputElement>(null);

  const handleFilesAdded = (files: FileList | null) => {
    if (!files) return;
    const newFiles = Array.from(files);
    setSelectedFiles((prev) => [...prev, ...newFiles]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    setManifest(null);
    setError(null);
  };

  const totalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setError(null);
    setUploadProgress(15);

    try {
      setUploadProgress(40);
      const manifestRes = await api.uploadBulkFiles(
        selectedFiles,
        batchName.trim() || undefined,
        true,
        autoStart
      );
      setUploadProgress(100);
      setManifest(manifestRes);

      if (autoStart && manifestRes.batch_id) {
        await api.startBatch(manifestRes.batch_id);
      }

      if (onBatchCreated && manifestRes.batch_id) {
        onBatchCreated(manifestRes.batch_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute bulk upload.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Setup Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-100 mb-2">High-Volume File Ingestion</h2>
        <p className="text-sm text-slate-400 mb-6">
          Upload thousands of files or entire directories with streaming deduplication, content integrity hashing, and automated prioritization.
        </p>

        {/* Configuration Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Batch Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Q4 Invoices & Contracts"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Queue Priority Tier</label>
            <select
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={90}>Interactive Tier (Priority 90)</option>
              <option value={50}>Normal Tier (Priority 50)</option>
              <option value={30}>Bulk Ingestion (Priority 30)</option>
              <option value={10}>Maintenance / Low (Priority 10)</option>
            </select>
          </div>

          <div className="flex items-center space-x-3 pt-6">
            <label className="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={autoStart}
                onChange={(e) => setAutoStart(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500"
              />
              <span>Auto-start pipeline on upload</span>
            </label>
          </div>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
            isDragging
              ? "border-indigo-500 bg-indigo-500/10"
              : "border-slate-700 hover:border-slate-600 bg-slate-800/40"
          }`}
        >
          <div className="flex justify-center mb-3">
            <svg
              className="w-12 h-12 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <p className="text-sm font-medium text-slate-200 mb-1">
            Drag & drop files or entire directory folders here
          </p>
          <p className="text-xs text-slate-400 mb-4">
            Supports PDF, DOCX, XLSX, PPTX, MP3, WAV, MP4, JSON, CSV, ZIP, TAR, Code, and Images up to 500 MB per file
          </p>

          <div className="flex justify-center space-x-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg shadow transition-colors"
            >
              Browse Files
            </button>
            <button
              type="button"
              onClick={() => dirInputRef.current?.click()}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium rounded-lg shadow transition-colors"
            >
              Select Directory Folder
            </button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFilesAdded(e.target.files)}
          />
          <input
            ref={dirInputRef}
            type="file"
            multiple
            // @ts-expect-error webkitdirectory is standard in browsers but not typed in React default attributes
            webkitdirectory="true"
            className="hidden"
            onChange={(e) => handleFilesAdded(e.target.files)}
          />
        </div>

        {/* Selected Files Staging List */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 border-t border-slate-800 pt-4">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-slate-200">
                Staged Files: <span className="text-indigo-400 font-semibold">{selectedFiles.length}</span> ({formatBytes(totalSize)})
              </span>
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs text-rose-400 hover:text-rose-300 transition-colors"
              >
                Clear All
              </button>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-1.5 pr-2">
              {selectedFiles.slice(0, 100).map((file, idx) => (
                <div
                  key={`${file.name}-${idx}`}
                  className="flex items-center justify-between bg-slate-800/60 px-3 py-1.5 rounded text-xs text-slate-300"
                >
                  <span className="truncate max-w-md">{file.name}</span>
                  <div className="flex items-center space-x-3 shrink-0">
                    <span className="text-slate-500">{formatBytes(file.size)}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      className="text-slate-400 hover:text-rose-400"
                    >
                      &times;
                    </button>
                  </div>
                </div>
              ))}
              {selectedFiles.length > 100 && (
                <p className="text-xs text-slate-400 text-center py-2">
                  ...and {selectedFiles.length - 100} more files
                </p>
              )}
            </div>

            {/* Upload Button */}
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white text-sm font-semibold rounded-lg shadow-md transition-colors flex items-center space-x-2"
              >
                {uploading ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Ingesting Files ({uploadProgress}%)...</span>
                  </>
                ) : (
                  <span>Submit Batch Ingestion ({selectedFiles.length} files)</span>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm">
          <strong>Ingestion Error:</strong> {error}
        </div>
      )}

      {/* Manifest Summary Result */}
      {manifest && (
        <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <h3 className="text-base font-semibold text-slate-100">
                Batch Registered: {manifest.batch_name}
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">ID: {manifest.batch_id}</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-slate-800/60 p-3 rounded-lg">
              <span className="block text-xs text-slate-400">Total Submitted</span>
              <span className="text-lg font-bold text-slate-200">{manifest.total_submitted}</span>
            </div>
            <div className="bg-slate-800/60 p-3 rounded-lg">
              <span className="block text-xs text-emerald-400">Accepted</span>
              <span className="text-lg font-bold text-emerald-400">{manifest.total_accepted}</span>
            </div>
            <div className="bg-slate-800/60 p-3 rounded-lg">
              <span className="block text-xs text-amber-400">Deduplicated (Reused)</span>
              <span className="text-lg font-bold text-amber-400">{manifest.total_reused}</span>
            </div>
            <div className="bg-slate-800/60 p-3 rounded-lg">
              <span className="block text-xs text-rose-400">Rejected / Failed</span>
              <span className="text-lg font-bold text-rose-400">{manifest.total_rejected}</span>
            </div>
          </div>

          <p className="text-xs text-slate-400">
            {manifest.auto_started
              ? "Jobs have been prioritized and queued across worker nodes."
              : "Batch is in pending state. Navigate to the Batches tab to start execution."}
          </p>
        </div>
      )}
    </div>
  );
};
