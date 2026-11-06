import React from "react";
import { Sparkles } from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { AIWorkspace } from "@/components/ai/AIWorkspace";

export const AIIntelligencePage: React.FC = () => {
  return (
    <PageContainer
      title="Universal AI Intelligence"
      subtitle="Cross-format RAG, semantic hybrid search, multi-file chat, summarization, and verifiable citation grounding."
      action={
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-xs font-semibold">
          <Sparkles className="h-4 w-4" />
          <span>Sovereign &amp; Multimodal</span>
        </div>
      }
    >
      <AIWorkspace />
    </PageContainer>
  );
};
