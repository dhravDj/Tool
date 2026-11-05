import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "@/layouts/MainLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { FileLibraryPage } from "@/pages/FileLibraryPage";
import { ProcessingJobsPage } from "@/pages/ProcessingJobsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { SystemStatusPage } from "@/pages/SystemStatusPage";
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
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/jobs" element={<ProcessingJobsPage />} />
            <Route path="/files" element={<FileLibraryPage />} />
            <Route path="/system" element={<SystemStatusPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
