import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { KnowledgeSearchView } from "@/components/ai/KnowledgeSearchView";
import { Badge } from "@/components/ui/Badge";
import { PageContainer } from "@/components/ui/PageContainer";
import { api } from "@/services/api";

export const KnowledgeSearchPage: React.FC = () => {
  const { data: analytics } = useQuery({
    queryKey: ["dashboardAnalytics"],
    queryFn: api.getDashboardAnalytics,
    staleTime: 30000,
  });

  const aiStats = analytics?.ai_summary;

  return (
    <PageContainer
      title="Knowledge Library & Hybrid Search"
      subtitle="Reciprocal Rank Fusion combining BM25 keyword matching with dense vector cosine embeddings"
      action={
        <div className="flex items-center gap-2">
          {aiStats && (
            <Badge variant="primary" size="md">
              <Sparkles className="h-3 w-3 mr-1 text-purple-500" />
              {aiStats.indexed_documents} Files Indexed ({aiStats.indexed_chunks.toLocaleString()} chunks)
            </Badge>
          )}
        </div>
      }
    >
      <div className="rounded-2xl border border-border bg-card p-6 shadow-2xs">
        <KnowledgeSearchView />
      </div>
    </PageContainer>
  );
};
