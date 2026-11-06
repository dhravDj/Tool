"""Structured Data Content Adapter (Phase 9: JSON, XML, YAML, TOML, Parquet, AVRO)."""

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class StructuredDataContentAdapter(BaseContentAdapter):
    """Adapts Phase 9 StructuredDataDocument into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        sd_dict = data.model_dump() if isinstance(data, BaseModel) else data
        fmt = sd_dict.get("format") or "structured"
        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        seen_citations: set[str] = set()
        full_text_parts: list[str] = []

        # 1. Schema definition / fields
        schema_def = sd_dict.get("schema_definition") or {}
        if schema_def:
            schema_json = json.dumps(schema_def, indent=2)
            schema_text = f"Schema Definition ({fmt.upper()}):\n{schema_json}"
            citation = f"{filename} — Schema Definition"
            full_text_parts.append(schema_text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="structured_data",
                formatted_citation=citation,
                metadata={"section": "schema_definition"},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"sd_{file_id[:8]}_schema",
                    content=schema_text,
                    block_type="data_profile",
                    source_reference=src_ref,
                    token_estimate=max(1, len(schema_text.split())),
                    metadata={"format": fmt, "type": "schema"},
                )
            )

        # 2. Data profiling per column/field
        data_profile = sd_dict.get("data_profile") or {}
        columns = data_profile.get("columns") or []
        for idx, col in enumerate(columns):
            col_name = col.get("name") or f"column_{idx}"
            col_type = col.get("inferred_type") or "unknown"
            col_stats = col.get("statistics") or {}
            profile_lines = [
                f"Field / Column: {col_name}",
                f"Type: {col_type}",
                f"Null Count: {col_stats.get('null_count', 0)} ({col_stats.get('null_percentage', 0.0):.1f}%)",
                f"Unique Values: {col_stats.get('unique_count', 'N/A')}",
            ]
            if "min" in col_stats and "max" in col_stats:
                profile_lines.append(f"Range: [{col_stats['min']} to {col_stats['max']}]")
            if "sample_values" in col_stats and col_stats["sample_values"]:
                samples_str = ", ".join(str(s) for s in col_stats["sample_values"][:5])
                profile_lines.append(f"Sample Values: {samples_str}")

            col_text = "\n".join(profile_lines)
            citation = f"{filename} — Field: {col_name}"
            full_text_parts.append(col_text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="structured_data",
                formatted_citation=citation,
                json_path=f"$.{col_name}",
                metadata={"column": col_name},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"sd_{file_id[:8]}_col_{idx}_{col_name}",
                    content=col_text,
                    block_type="data_profile",
                    source_reference=src_ref,
                    token_estimate=max(1, len(col_text.split())),
                    metadata={"column": col_name, "inferred_type": col_type},
                )
            )

        # 3. Sample records / preview
        records = sd_dict.get("records") or []
        if records:
            sample_slice = records[:10]
            preview_json = json.dumps(sample_slice, indent=2)
            preview_text = f"Sample Records (Rows 1–{len(sample_slice)}):\n{preview_json}"
            citation = f"{filename} — Records 1–{len(sample_slice)}"
            full_text_parts.append(preview_text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="structured_data",
                formatted_citation=citation,
                paragraph_index=1,
                metadata={"record_count": len(sample_slice)},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"sd_{file_id[:8]}_records_preview",
                    content=preview_text,
                    block_type="table",
                    source_reference=src_ref,
                    token_estimate=max(1, len(preview_text.split())),
                    metadata={"sample_count": len(sample_slice)},
                )
            )

        # 4. Fallback: raw preview or summary
        if not content_blocks:
            raw_preview = sd_dict.get("raw_preview") or ""
            text = (
                f"Structured File {filename} ({fmt.upper()}). "
                f"Root Type: {sd_dict.get('root_type', 'object')}. "
                f"Validation: {'Valid' if sd_dict.get('validation_results', {}).get('is_valid', True) else 'Invalid'}."
            )
            if raw_preview:
                text += f"\nPreview:\n{raw_preview[:1500]}"
            full_text_parts.append(text)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="structured_data",
                formatted_citation=f"{filename} — Overview",
            )
            source_refs.append(src_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"sd_{file_id[:8]}_overview",
                    content=text,
                    block_type="metadata",
                    source_reference=src_ref,
                    token_estimate=max(1, len(text.split())),
                )
            )

        combined_text = "\n".join(full_text_parts)
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_struct_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="structured_data",
            content_type=fmt,
            title=filename,
            content_blocks=content_blocks,
            metadata={
                "format": fmt,
                "root_type": sd_dict.get("root_type", "object"),
                "field_count": len(columns),
                "record_count": data_profile.get("total_rows", len(records)),
            },
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
