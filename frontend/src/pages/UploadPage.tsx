import React, { useState } from "react";
import { FileUp, ShieldCheck, UploadCloud } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageContainer } from "@/components/ui/PageContainer";

export const UploadPage: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <PageContainer
      title="Upload & Ingestion Gateway"
      subtitle="Ingest documents, archives, or media for universal processing"
    >
      {/* Security Architecture Callout */}
      <div className="rounded-xl border border-border bg-card p-4 flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
        <div className="text-xs text-muted-foreground space-y-1">
          <p className="font-semibold text-foreground">Zero-Trust File Handling Safeguards</p>
          <p>
            All uploaded binaries undergo multi-stage validation: magic byte signature verification,
            strict extension checks, SHA-256 fingerprinting, and sandboxed storage isolation.
            Uploaded files are never executed directly.
          </p>
        </div>
      </div>

      {/* Upload Drop Zone (Visual Shell) */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        className={`mt-6 border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
          isDragging
            ? "border-primary bg-primary/5 scale-[0.99]"
            : "border-border bg-card/60 hover:border-primary/50"
        }`}
      >
        <div className="flex flex-col items-center justify-center max-w-md mx-auto">
          <div className="p-4 rounded-full bg-primary/10 text-primary mb-4">
            <UploadCloud className="h-10 w-10" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">
            Drag and drop files to ingest
          </h3>
          <p className="text-xs text-muted-foreground mt-2">
            Supports PDF, DOCX, XLSX, Images, Audio, Archives, and Code files up to 100 MB per file.
          </p>

          <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
            <label className="cursor-pointer rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-primary/90 transition">
              Browse Local Files
              <input type="file" multiple className="hidden" disabled />
            </label>
            <span className="text-xs text-muted-foreground">or create batch via API</span>
          </div>

          <p className="text-[11px] text-muted-foreground/80 mt-4 italic">
            * Note: Live file ingestion engines will be connected in Phase 2.
          </p>
        </div>
      </div>

      {/* Ingestion Queue Empty State */}
      <div className="mt-8 rounded-xl border border-border bg-card p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Pending Upload Queue</h3>
        <EmptyState
          icon={<FileUp className="h-8 w-8" />}
          title="Upload Queue Empty"
          description="Files selected for ingestion will appear here with checksum, detected MIME, and transfer status."
        />
      </div>
    </PageContainer>
  );
};
