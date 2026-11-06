import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { UniversalFileInspector } from "@/components/inspector/UniversalFileInspector";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PageContainer } from "@/components/ui/PageContainer";
import { api } from "@/services/api";

export const UniversalInspectorPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();

  const {
    data: files,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["files"],
    queryFn: () => api.getFiles(100, 0),
  });

  if (isLoading) {
    return <LoadingState message="Loading file metadata and inspection engine..." />;
  }

  const targetFile = (files || []).find((f) => f.id === fileId);

  if (error || !targetFile) {
    return (
      <PageContainer title="File Inspector" subtitle="File details and analysis">
        <ErrorState
          title="File Not Found"
          message={`Unable to find file with ID "${fileId}". It may have been removed or does not exist.`}
          onRetry={() => refetch()}
        />
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate("/files")}
            className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline font-medium"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Return to File Library
          </button>
        </div>
      </PageContainer>
    );
  }

  return (
    <div className="p-4 sm:p-6 h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex-1 min-h-0">
        <UniversalFileInspector file={targetFile} onClose={() => navigate("/files")} />
      </div>
    </div>
  );
};
