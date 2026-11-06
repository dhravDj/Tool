"""Markdown report generator for Archive Intelligence Engine."""

from app.modules.archive_intelligence.generators.tree_generator import ArchiveTreeGenerator
from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveMarkdownGenerator:
    """Generates structured GitHub-flavored Markdown analysis reports."""

    def __init__(self) -> None:
        self.tree_gen = ArchiveTreeGenerator()

    def generate(self, doc: ArchiveDocument) -> str:
        meta = doc.metadata
        filename = meta.get("filename", f"Archive {doc.archive_id[:8]}")

        # Compute category distribution
        cat_counts: dict[str, int] = {}
        for entry in doc.entries:
            if not entry.is_directory:
                cat = entry.detection_result.get("category", "unknown")
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

        md: list[str] = [
            f"# Archive Intelligence Report: `{filename}`",
            "",
            "## 1. Overview & Provenance",
            "",
            "| Property | Value |",
            "|---|---|",
            f"| **Archive ID** | `{doc.archive_id}` |",
            f"| **Format** | `{doc.archive_format.upper()}` |",
            f"| **Processing Mode** | `{doc.processing_mode}` |",
            f"| **Processing Status** | `{doc.processing_status.upper()}` |",
            f"| **Total Entries** | {doc.total_entry_count:,} |",
            f"| **Files / Folders** | {meta.get('file_count', 0):,} files / {meta.get('directory_count', 0):,} folders |",
            f"| **Total Uncompressed Size** | {meta.get('total_uncompressed_size', 0):,} bytes |",
            f"| **Extracted Size** | {doc.extracted_size:,} bytes |",
            f"| **Compression Ratio** | {meta.get('compression_ratio', 1.0)}:1 |",
            f"| **Nested Archives** | {len(doc.nested_archives)} |",
            f"| **Encrypted** | `{meta.get('is_encrypted', False)}` |",
            f"| **Corrupted** | `{meta.get('is_corrupted', False)}` |",
            "",
        ]

        # Security Section
        sr = doc.safety_report
        has_security_flags = (
            sr.path_traversal_blocked > 0
            or sr.symlink_entries_blocked > 0
            or sr.suspicious_entries > 0
            or sr.compression_ratio_exceeded
            or sr.size_limit_exceeded
        )
        if has_security_flags:
            md.extend(
                [
                    "> [!WARNING]",
                    "> **Security Alerts Triggered**:",
                    f"> - Path Traversals Blocked: {sr.path_traversal_blocked}",
                    f"> - Symlinks / Link Escapes Blocked: {sr.symlink_entries_blocked}",
                    f"> - Suspicious Entries (Device files/FIFOs): {sr.suspicious_entries}",
                    f"> - Archive Bomb Flagged: {sr.compression_ratio_exceeded}",
                    f"> - Size Limit Exceeded: {sr.size_limit_exceeded}",
                    "",
                ]
            )
        else:
            md.extend(
                [
                    "> [!NOTE]",
                    "> Archive passed defensive safety validations: no directory traversals, symlink escapes, or excessive compression ratios detected.",
                    "",
                ]
            )

        # Category Breakdown
        md.extend(
            [
                "## 2. File Type Distribution",
                "",
                "| Category | Count | Percentage |",
                "|---|---|---|",
            ]
        )
        total_files = meta.get("file_count", 0) or 1
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
            pct = (cnt / total_files) * 100
            md.append(f"| **{cat.capitalize()}** | {cnt} | {pct:.1f}% |")
        md.append("")

        # Directory Hierarchy
        tree_text = self.tree_gen.generate(doc.hierarchy)
        md.extend(
            [
                "## 3. Archive Directory Hierarchy",
                "",
                "```text",
                tree_text,
                "```",
                "",
            ]
        )

        # Top entries table
        md.extend(
            [
                "## 4. Entry Manifest (First 25)",
                "",
                "| Entry ID | Original Path | Size (B) | Type | Status |",
                "|---|---|---|---|---|",
            ]
        )
        for entry in doc.entries[:25]:
            sz = entry.uncompressed_size
            md.append(
                f"| `{entry.entry_id[:8]}` | `{entry.original_path}` | {sz:,} | {entry.entry_type} | `{entry.processing_status}` |"
            )
        if len(doc.entries) > 25:
            md.append(f"\n*...and {len(doc.entries) - 25} additional entries.*")
        md.append("")

        return "\n".join(md)
