"""Archive Content Adapter (Phase 10: ZIP, TAR, GZ, 7Z, RAR, BZ2, XZ, ISO, DEB, RPM)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class ArchiveContentAdapter(BaseContentAdapter):
    """Adapts Phase 10 ArchiveDocument into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        arch_dict = data.model_dump() if isinstance(data, BaseModel) else data
        arch_format = arch_dict.get("archive_format") or "archive"
        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        seen_citations: set[str] = set()
        full_text_parts: list[str] = []

        entries = arch_dict.get("entries", [])
        # 1. Archive Manifest / Entries
        if entries:
            manifest_lines = []
            for idx, entry in enumerate(entries[:100]):
                epath = entry.get("path") or entry.get("name") or f"entry_{idx}"
                esize = entry.get("uncompressed_size") or entry.get("size") or 0
                is_dir = entry.get("is_dir", False)
                kind = "Directory" if is_dir else "File"
                manifest_lines.append(f"- {kind}: {epath} ({esize:,} bytes)")

                # If entry is an important file (not dir), add specific citation
                if not is_dir and idx < 25:
                    citation = f"{filename} — Member: {epath}"
                    src_ref = SourceReference(
                        source_file_id=file_id,
                        original_filename=filename,
                        source_type="archive",
                        formatted_citation=citation,
                        archive_path=epath,
                    )
                    if citation not in seen_citations:
                        source_refs.append(src_ref)
                        seen_citations.add(citation)

            manifest_text = f"Archive Manifest for {filename} ({len(entries)} items):\n" + "\n".join(manifest_lines)
            full_text_parts.append(manifest_text)

            gen_citation = f"{filename} — Archive Manifest"
            gen_src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="archive",
                formatted_citation=gen_citation,
                metadata={"section": "manifest"},
            )
            if gen_citation not in seen_citations:
                source_refs.append(gen_src_ref)
                seen_citations.add(gen_citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"arch_{file_id[:8]}_manifest",
                    content=manifest_text,
                    block_type="table",
                    source_reference=gen_src_ref,
                    token_estimate=max(1, len(manifest_text.split())),
                    metadata={"total_entries": len(entries), "archive_format": arch_format},
                )
            )

        # 2. Safety Assessment
        safety = arch_dict.get("safety_report") or {}
        if safety:
            is_safe = safety.get("is_safe", True)
            warnings = safety.get("warnings") or []
            flags = safety.get("flags") or []
            safety_text = (
                f"Archive Security & Safety Report for {filename}:\n"
                f"- Safety Verdict: {'PASSED (Safe)' if is_safe else 'SECURITY ALERTS DETECTED'}\n"
                f"- Max Nesting Depth: {arch_dict.get('nesting_depth', 1)}\n"
                f"- Extracted Size: {arch_dict.get('extracted_size', 0):,} bytes\n"
            )
            if warnings:
                safety_text += f"- Warnings: {', '.join(warnings)}\n"
            if flags:
                safety_text += f"- Flags: {', '.join(flags)}\n"

            citation = f"{filename} — Safety Assessment"
            full_text_parts.append(safety_text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="archive",
                formatted_citation=citation,
                metadata={"section": "safety_assessment"},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"arch_{file_id[:8]}_safety",
                    content=safety_text,
                    block_type="metadata",
                    source_reference=src_ref,
                    token_estimate=max(1, len(safety_text.split())),
                    metadata={"is_safe": is_safe},
                )
            )

        # Fallback if no entries
        if not content_blocks:
            overview_text = (
                f"Archive {filename} (Format: {arch_format.upper()}, "
                f"Entries: {arch_dict.get('total_entry_count', len(entries))}, "
                f"Status: {arch_dict.get('processing_status', 'completed')})"
            )
            full_text_parts.append(overview_text)
            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="archive",
                formatted_citation=f"{filename} — Overview",
            )
            source_refs.append(src_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"arch_{file_id[:8]}_overview",
                    content=overview_text,
                    block_type="metadata",
                    source_reference=src_ref,
                    token_estimate=max(1, len(overview_text.split())),
                )
            )

        combined_text = "\n".join(full_text_parts)
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_arch_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="archive",
            content_type=arch_format,
            title=filename,
            content_blocks=content_blocks,
            metadata={
                "archive_format": arch_format,
                "total_entry_count": arch_dict.get("total_entry_count", len(entries)),
                "extracted_size": arch_dict.get("extracted_size", 0),
                "nesting_depth": arch_dict.get("nesting_depth", 1),
            },
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
