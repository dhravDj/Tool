import React, { useState } from "react";
import { Cpu, HardDrive, Shield } from "lucide-react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { PageContainer } from "@/components/ui/PageContainer";

export const SettingsPage: React.FC = () => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  return (
    <PageContainer
      title="Platform Settings"
      subtitle="Runtime configuration, AI inference parameters, and security policies"
    >
      <div className="space-y-6 max-w-4xl">
        {/* AI Inference Policy */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-3 border-b border-border pb-4 mb-4">
            <Cpu className="h-5 w-5 text-indigo-500" />
            <div>
              <h3 className="text-base font-semibold text-foreground">AI Inference Architecture</h3>
              <p className="text-xs text-muted-foreground">Configure local vs cloud model processing</p>
            </div>
          </div>

          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/40">
              <div>
                <p className="font-semibold text-foreground">Default Execution Mode</p>
                <p className="text-muted-foreground mt-0.5">
                  Keep processing strictly local on-premises to guarantee data sovereignty.
                </p>
              </div>
              <span className="font-mono px-2.5 py-1 rounded bg-muted border border-border font-bold">
                LOCAL (Ollama / CPU)
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/40">
              <div>
                <p className="font-semibold text-foreground">Cloud Processing Consent</p>
                <p className="text-muted-foreground mt-0.5">
                  Allow transmitting document content to external AI APIs (Gemini, Anthropic, OpenAI).
                </p>
              </div>
              <span className="font-mono text-rose-500 font-semibold px-2 py-0.5 bg-rose-500/10 rounded">
                DISABLED BY DEFAULT
              </span>
            </div>
          </div>
        </div>

        {/* Storage Configuration */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-3 border-b border-border pb-4 mb-4">
            <HardDrive className="h-5 w-5 text-emerald-500" />
            <div>
              <h3 className="text-base font-semibold text-foreground">Storage Layer</h3>
              <p className="text-xs text-muted-foreground">Manage file persistence and temporary scratchpad</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-muted/40">
              <span className="text-muted-foreground">Storage Provider</span>
              <p className="font-semibold text-foreground mt-1">Local Filesystem Adapter</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/40">
              <span className="text-muted-foreground">Maximum Upload Limit</span>
              <p className="font-semibold text-foreground mt-1">100 MB per file</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/40">
              <span className="text-muted-foreground">Temporary Retention</span>
              <p className="font-semibold text-foreground mt-1">Purged immediately on job finish</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/40">
              <span className="text-muted-foreground">Object Storage (S3 / MinIO)</span>
              <p className="font-semibold text-foreground mt-1">Ready for Phase 2 activation</p>
            </div>
          </div>
        </div>

        {/* Security & Access Controls */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-3 border-b border-border pb-4 mb-4">
            <Shield className="h-5 w-5 text-primary" />
            <div>
              <h3 className="text-base font-semibold text-foreground">Security Safeguards</h3>
              <p className="text-xs text-muted-foreground">Platform defense and access restrictions</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-border/40">
              <span className="text-foreground font-medium">Magic Byte Signature Validation</span>
              <span className="text-emerald-500 font-semibold">Enforced</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border/40">
              <span className="text-foreground font-medium">Strict Extension Mismatch Check</span>
              <span className="text-emerald-500 font-semibold">Enforced</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border/40">
              <span className="text-foreground font-medium">Path Traversal Sanitization</span>
              <span className="text-emerald-500 font-semibold">Active</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-foreground font-medium">Zip Bomb Decompression Protection</span>
              <span className="text-emerald-500 font-semibold">Active</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border flex justify-end">
            <button
              onClick={() => setShowConfirmDialog(true)}
              className="px-4 py-2 rounded-lg bg-muted text-foreground text-xs font-semibold hover:bg-muted/80 transition"
            >
              Test Confirmation Dialog
            </button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showConfirmDialog}
        title="Sample Confirmation Dialog"
        description="This demonstrates the accessible, reusable confirmation modal component built for future destructive actions."
        onConfirm={() => setShowConfirmDialog(false)}
        onCancel={() => setShowConfirmDialog(false)}
      />
    </PageContainer>
  );
};
