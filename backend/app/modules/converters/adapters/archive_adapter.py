"""Archive adapter converting ArchiveDocument to UniversalContent."""

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument
from app.modules.converters.schemas import (
    UniversalCodeBlock,
    UniversalContent,
    UniversalSection,
    UniversalTable,
)


class ArchiveAdapter:
    """Adapts ArchiveDocument into standard UniversalContent capturing hierarchy, entry tables, and safety reports."""

    @classmethod
    def adapt(cls, doc: ArchiveDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or f"archive.{doc.archive_format}"
        tables: list[UniversalTable] = []
        sections: list[UniversalSection] = []
        code_blocks: list[UniversalCodeBlock] = []

        # 1. Entry Manifest Table
        entry_rows: list[list[str]] = []
        total_uncompressed = 0
        total_compressed = 0

        for entry in doc.entries:
            total_uncompressed += entry.uncompressed_size
            total_compressed += entry.compressed_size
            ratio = (
                f"{(entry.compressed_size / entry.uncompressed_size * 100):.1f}%"
                if entry.uncompressed_size > 0
                else "-"
            )
            fmt = entry.detection_result.get("format_id") or entry.extension or "unknown"
            entry_rows.append(
                [
                    entry.normalized_path,
                    entry.entry_type,
                    fmt,
                    f"{entry.uncompressed_size:,} B",
                    f"{entry.compressed_size:,} B",
                    ratio,
                    "Yes" if entry.encrypted else "No",
                ]
            )

        tables.append(
            UniversalTable(
                title=f"Archive Contents Manifest ({len(doc.entries)} entries)",
                headers=["Path", "Type", "Format", "Uncompressed", "Compressed", "Ratio", "Encrypted"],
                rows=entry_rows,
                row_count=len(entry_rows),
                col_count=7,
            )
        )

        # 2. Directory Tree hierarchy
        tree_lines: list[str] = []

        def build_tree(node, prefix=""):
            for idx, child in enumerate(node.children):
                is_last = idx == len(node.children) - 1
                connector = "└── " if is_last else "├── "
                sub_prefix = "    " if is_last else "│   "
                tag = "/" if child.is_directory else ""
                tree_lines.append(f"{prefix}{connector}{child.name}{tag}")
                if child.children:
                    build_tree(child, prefix + sub_prefix)

        tree_lines.append(filename + "/")
        if doc.hierarchy:
            build_tree(doc.hierarchy)

        tree_str = "\n".join(tree_lines)
        code_blocks.append(
            UniversalCodeBlock(
                language="text",
                code=tree_str,
                caption=f"Archive Hierarchy ({filename})",
                line_count=len(tree_lines),
            )
        )

        sections.append(
            UniversalSection(
                title="Archive Folder Hierarchy",
                level=2,
                content=f"```\n{tree_str}\n```",
            )
        )

        # Safety warnings
        warnings = list(doc.warnings)
        if hasattr(doc, "safety_report") and doc.safety_report:
            warnings.extend(doc.safety_report.warnings)

        meta = {
            "format": doc.archive_format,
            "entry_count": len(doc.entries),
            "total_uncompressed_bytes": total_uncompressed,
            "total_compressed_bytes": total_compressed,
            "nested_archives_count": len(doc.nested_archives),
        }

        raw_text = (
            f"Archive: {filename} ({doc.archive_format.upper()})\n"
            f"Total Entries: {len(doc.entries)} | Uncompressed: {total_uncompressed:,} bytes\n\n"
            f"{tree_str}\n"
        )

        return UniversalContent(
            source_filename=filename,
            source_format=doc.archive_format,
            title=f"Archive: {filename}",
            author="",
            page_count=1,
            word_count=len(raw_text.split()),
            paragraphs=[],
            sections=sections,
            tables=tables,
            code_blocks=code_blocks,
            metadata=meta,
            warnings=warnings,
            raw_text=raw_text,
        )
