"""Spreadsheet Content Adapter (Phase 5: XLSX, XLS, CSV, TSV, ODS)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class SpreadsheetContentAdapter(BaseContentAdapter):
    """Adapts Phase 5 SpreadsheetDocument structures into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        sheet_doc = data.model_dump() if isinstance(data, BaseModel) else data
        sheets = sheet_doc.get("sheets") or []

        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        full_text_parts: list[str] = []

        for s_idx, s in enumerate(sheets):
            sheet_name = s.get("name") or s.get("sheet_name") or f"Sheet{s_idx + 1}"
            row_count = s.get("row_count", 0)
            col_count = s.get("column_count", 0)

            # 1. Sheet Overview Block
            overview_txt = f"Sheet: {sheet_name} ({row_count} rows, {col_count} columns)"
            full_text_parts.append(overview_txt)
            sheet_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="spreadsheet",
                formatted_citation=f"{filename} — Sheet: {sheet_name}",
                sheet_name=sheet_name,
            )
            source_refs.append(sheet_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"sheet_{file_id[:8]}_s{s_idx}_meta",
                    content=overview_txt,
                    block_type="heading",
                    source_reference=sheet_ref,
                    token_estimate=max(1, len(overview_txt.split())),
                    metadata={"sheet_name": sheet_name, "rows": row_count, "cols": col_count},
                )
            )

            # 2. Table or Header & Data Blocks
            tables = s.get("tables") or []
            if tables:
                for t_idx, t in enumerate(tables):
                    t_name = t.get("name") or f"Table {t_idx + 1}"
                    t_range = t.get("range", "A1")
                    headers = t.get("headers") or []
                    rows = t.get("sample_rows") or t.get("rows") or []

                    table_lines = [f"Table: {t_name} (Range: {t_range})"]
                    if headers:
                        table_lines.append("Columns: " + " | ".join(str(h) for h in headers))
                    for r in rows[:25]:  # Bounded row preview per table
                        if isinstance(r, dict):
                            table_lines.append(" | ".join(f"{k}: {v}" for k, v in r.items() if v is not None))
                        elif isinstance(r, list):
                            table_lines.append(" | ".join(str(c) for c in r if c is not None))

                    t_text = "\n".join(table_lines)
                    full_text_parts.append(t_text)

                    table_ref = SourceReference(
                        source_file_id=file_id,
                        original_filename=filename,
                        source_type="spreadsheet",
                        formatted_citation=f"{filename} — Sheet: {sheet_name}, Cells {t_range}",
                        sheet_name=sheet_name,
                        cell_range=t_range,
                    )
                    source_refs.append(table_ref)
                    content_blocks.append(
                        ContentBlock(
                            block_id=f"sheet_{file_id[:8]}_s{s_idx}_t{t_idx}",
                            content=t_text,
                            block_type="table",
                            source_reference=table_ref,
                            token_estimate=max(1, len(t_text.split())),
                            metadata={"table_name": t_name, "range": t_range},
                        )
                    )

            # 3. Direct Rows Fallback if no extracted table structures
            elif s.get("rows"):
                raw_rows = s.get("rows", [])
                chunk_size = 20
                for r_i in range(0, min(len(raw_rows), 100), chunk_size):
                    slice_rows = raw_rows[r_i : r_i + chunk_size]
                    range_label = f"A{r_i + 1}:Z{r_i + len(slice_rows)}"
                    row_strs = [" | ".join(str(c) for c in r) for r in slice_rows]
                    r_text = f"Sheet: {sheet_name} ({range_label})\n" + "\n".join(row_strs)
                    full_text_parts.append(r_text)

                    r_ref = SourceReference(
                        source_file_id=file_id,
                        original_filename=filename,
                        source_type="spreadsheet",
                        formatted_citation=f"{filename} — Sheet: {sheet_name}, Cells {range_label}",
                        sheet_name=sheet_name,
                        cell_range=range_label,
                    )
                    source_refs.append(r_ref)
                    content_blocks.append(
                        ContentBlock(
                            block_id=f"sheet_{file_id[:8]}_s{s_idx}_r{r_i}",
                            content=r_text,
                            block_type="table",
                            source_reference=r_ref,
                            token_estimate=max(1, len(r_text.split())),
                        )
                    )

            # 4. Column Profiles / Statistical Understanding
            col_profiles = s.get("column_profiles") or []
            if col_profiles:
                p_lines = [f"Data Profiles for Sheet '{sheet_name}':"]
                for p in col_profiles:
                    name = p.get("name") or p.get("column_name", "Column")
                    dtype = p.get("data_type", "unknown")
                    stats = p.get("statistics") or {}
                    p_lines.append(f"• {name} ({dtype}): nulls={stats.get('null_count', 0)}, distinct={stats.get('distinct_count', 'N/A')}")
                p_text = "\n".join(p_lines)
                full_text_parts.append(p_text)
                p_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="spreadsheet",
                    formatted_citation=f"{filename} — Sheet: {sheet_name}, Column Profiles",
                    sheet_name=sheet_name,
                )
                source_refs.append(p_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"sheet_{file_id[:8]}_s{s_idx}_profiles",
                        content=p_text,
                        block_type="structured_record",
                        source_reference=p_ref,
                        token_estimate=max(1, len(p_text.split())),
                    )
                )

        combined_text = "\n\n".join(full_text_parts) or f"Spreadsheet: {filename}"
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_sheet_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="spreadsheet",
            content_type=sheet_doc.get("format", "spreadsheet"),
            title=filename,
            content_blocks=content_blocks,
            metadata=sheet_doc.get("metadata", {}),
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
