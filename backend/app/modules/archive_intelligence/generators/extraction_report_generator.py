"""Extraction audit and execution metrics report generator."""

import json

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveExtractionReportGenerator:
    """Generates detailed extraction report documenting extracted, blocked, and failed files."""

    def generate(self, doc: ArchiveDocument) -> str:
        report = {
            "archive_id": doc.archive_id,
            "processing_mode": doc.processing_mode,
            "status": doc.processing_status,
            "metrics": {
                "total_entries": doc.total_entry_count,
                "extracted_file_count": len(doc.extracted_files),
                "blocked_entry_count": len(doc.blocked_entries),
                "failed_entry_count": len(doc.failed_entries),
                "extracted_bytes": doc.extracted_size,
                "processing_duration_seconds": doc.processing_metadata.get("duration", 0.0),
            },
            "extracted_files": doc.extracted_files,
            "blocked_entries": doc.blocked_entries,
            "failed_entries": doc.failed_entries,
            "warnings": doc.warnings,
            "errors": doc.errors,
        }
        return json.dumps(report, indent=2)
