import React, { useState } from "react";
import { Files, Filter, Search } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageContainer } from "@/components/ui/PageContainer";

export const FileLibraryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const categories = [
    "all",
    "document",
    "spreadsheet",
    "presentation",
    "image",
    "audio",
    "video",
    "archive",
    "code",
  ];

  return (
    <PageContainer
      title="File Library"
      subtitle="Catalog of ingested files, extracted metadata, and generated assets"
    >
      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by filename, hash, or detected MIME..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-border bg-card pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 sm:pb-0">
          <Filter className="h-4 w-4 text-muted-foreground shrink-0 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`rounded-lg px-2.5 py-1.5 text-xs capitalize font-medium transition shrink-0 ${
                selectedCategory === cat
                  ? "bg-primary text-white"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Library Table Shell */}
      <div className="mt-6 rounded-xl border border-border bg-card p-6">
        <EmptyState
          icon={<Files className="h-8 w-8" />}
          title="File Library is Empty"
          description="Uploaded files and documents will be indexed and cataloged here in subsequent phases."
        />
      </div>
    </PageContainer>
  );
};
