"""Plain text summary generator for ArchiveDocument."""

from app.modules.archive_intelligence.generators.tree_generator import ArchiveTreeGenerator
from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchivePlainTextGenerator:
    """Generates human-readable plain text report."""

    def __init__(self) -> None:
        self.tree_gen = ArchiveTreeGenerator()

    def generate(self, doc: ArchiveDocument) -> str:
        meta = doc.metadata
        lines = [
            "=" * 70,
            f"DOCUMIND ARCHIVE REPORT: {meta.get('filename', doc.archive_id)}",
            "=" * 70,
            f"Archive ID:           {doc.archive_id}",
            f"Format:               {doc.archive_format.upper()}",
            f"Processing Mode:      {doc.processing_mode}",
            f"Processing Status:    {doc.processing_status.upper()}",
            f"Total Entries:        {doc.total_entry_count}",
            f"Files Count:          {meta.get('file_count', 0)}",
            f"Directories Count:    {meta.get('directory_count', 0)}",
            f"Nested Archives:      {len(doc.nested_archives)}",
            f"Extracted Files:      {len(doc.extracted_files)}",
            f"Blocked Entries:      {len(doc.blocked_entries)}",
            f"Failed Entries:       {len(doc.failed_entries)}",
            f"Total Uncompressed:   {meta.get('total_uncompressed_size', 0):,} bytes",
            f"Extracted Size:       {doc.extracted_size:,} bytes",
            f"Compression Ratio:    {meta.get('compression_ratio', 1.0)}:1",
            f"Is Encrypted:         {meta.get('is_encrypted', False)}",
            f"Is Corrupted:         {meta.get('is_corrupted', False)}",
            "",
            "--- SECURITY AUDIT ---",
            f"Path Traversals Blocked: {doc.safety_report.path_traversal_blocked}",
            f"Symlink Escapes Blocked: {doc.safety_report.symlink_entries_blocked}",
            f"Suspicious Entries:      {doc.safety_report.suspicious_entries}",
            f"Bomb Ratio Exceeded:     {doc.safety_report.compression_ratio_exceeded}",
            f"Size Quota Exceeded:     {doc.safety_report.size_limit_exceeded}",
            "",
            "--- DIRECTORY HIERARCHY ---",
            self.tree_gen.generate(doc.hierarchy),
            "",
            "--- RECENT WARNINGS ---",
        ]
        if doc.warnings or doc.safety_report.warnings:
            all_warnings = list(dict.fromkeys(doc.warnings + doc.safety_report.warnings))
            for w in all_warnings[:15]:
                lines.append(f"  * {w}")
        else:
            lines.append("  (None)")

        lines.append("=" * 70)
        return "\n".join(lines)
