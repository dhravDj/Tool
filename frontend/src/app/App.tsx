import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "@/context/ToastContext";
import { MainLayout } from "@/layouts/MainLayout";
import { BulkProcessingPage } from "@/pages/BulkProcessingPage";
import { ConversionHistoryPage } from "@/pages/ConversionHistoryPage";
import { ConvertPage } from "@/pages/ConvertPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { FileLibraryPage } from "@/pages/FileLibraryPage";
import { ProcessingJobsPage } from "@/pages/ProcessingJobsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { SystemStatusPage } from "@/pages/SystemStatusPage";
import { UniversalInspectorPage } from "@/pages/UniversalInspectorPage";
import { UploadPage } from "@/pages/UploadPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/convert" element={<ConvertPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/files" element={<FileLibraryPage />} />
              <Route path="/history" element={<ConversionHistoryPage />} />
              <Route path="/inspector/:fileId" element={<UniversalInspectorPage />} />
              <Route path="/bulk-processing" element={<BulkProcessingPage />} />
              <Route path="/jobs" element={<ProcessingJobsPage />} />
              <Route path="/system" element={<SystemStatusPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
};
