"""Presentation Content Adapter (Phase 6: PPTX, PPT, ODP)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class PresentationContentAdapter(BaseContentAdapter):
    """Adapts Phase 6 PresentationDocument structures into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        pres_doc = data.model_dump() if isinstance(data, BaseModel) else data
        slides = pres_doc.get("slides") or []

        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        full_text_parts: list[str] = []

        for s in slides:
            slide_num = s.get("slide_number", 1)
            title = (s.get("title") or "").strip()
            text_blocks = s.get("text_blocks") or []
            tables = s.get("tables") or []
            charts = s.get("charts") or []
            notes = (s.get("speaker_notes") or "").strip()

            slide_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="presentation",
                formatted_citation=f"{filename} — Slide {slide_num}",
                slide_number=slide_num,
            )
            source_refs.append(slide_ref)

            # Slide Title & Bullets
            slide_lines = [f"Slide {slide_num}: {title or '(Untitled Slide)'}"]
            for tb in text_blocks:
                txt = tb.get("text", "") if isinstance(tb, dict) else str(tb)
                if txt:
                    slide_lines.append(f"• {txt.strip()}")

            slide_text = "\n".join(slide_lines)
            full_text_parts.append(slide_text)
            content_blocks.append(
                ContentBlock(
                    block_id=f"pres_{file_id[:8]}_s{slide_num}_body",
                    content=slide_text,
                    block_type="slide",
                    source_reference=slide_ref,
                    token_estimate=max(1, len(slide_text.split())),
                    metadata={"slide_number": slide_num, "title": title},
                )
            )

            # Slide Tables
            for t_idx, t in enumerate(tables):
                headers = t.get("headers") or []
                rows = t.get("rows") or []
                t_lines = [f"Table on Slide {slide_num}:"]
                if headers:
                    t_lines.append(" | ".join(str(h) for h in headers))
                for r in rows:
                    t_lines.append(" | ".join(str(c) for c in r))
                t_str = "\n".join(t_lines)
                full_text_parts.append(t_str)

                t_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="presentation",
                    formatted_citation=f"{filename} — Slide {slide_num}, Table {t_idx + 1}",
                    slide_number=slide_num,
                )
                source_refs.append(t_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"pres_{file_id[:8]}_s{slide_num}_t{t_idx}",
                        content=t_str,
                        block_type="table",
                        source_reference=t_ref,
                        token_estimate=max(1, len(t_str.split())),
                    )
                )

            # Slide Charts
            for c_idx, c in enumerate(charts):
                c_title = c.get("title") or f"Chart {c_idx + 1}"
                c_type = c.get("chart_type", "chart")
                series = c.get("series") or []
                c_lines = [f"Chart on Slide {slide_num}: {c_title} ({c_type})"]
                for s_item in series:
                    s_name = s_item.get("name", "Series")
                    s_vals = s_item.get("values", [])
                    c_lines.append(f"  {s_name}: {s_vals}")
                c_str = "\n".join(c_lines)
                full_text_parts.append(c_str)

                c_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="presentation",
                    formatted_citation=f"{filename} — Slide {slide_num}, Chart: {c_title}",
                    slide_number=slide_num,
                )
                source_refs.append(c_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"pres_{file_id[:8]}_s{slide_num}_c{c_idx}",
                        content=c_str,
                        block_type="structured_record",
                        source_reference=c_ref,
                        token_estimate=max(1, len(c_str.split())),
                    )
                )

            # Speaker Notes
            if notes:
                n_str = f"Speaker Notes for Slide {slide_num}:\n{notes}"
                full_text_parts.append(n_str)
                notes_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="presentation",
                    formatted_citation=f"{filename} — Slide {slide_num}, Speaker Notes",
                    slide_number=slide_num,
                )
                source_refs.append(notes_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"pres_{file_id[:8]}_s{slide_num}_notes",
                        content=n_str,
                        block_type="paragraph",
                        source_reference=notes_ref,
                        token_estimate=max(1, len(n_str.split())),
                    )
                )

        combined_text = "\n\n".join(full_text_parts) or f"Presentation: {filename}"
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_pres_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="presentation",
            content_type=pres_doc.get("format", "presentation"),
            title=filename,
            content_blocks=content_blocks,
            metadata=pres_doc.get("metadata", {}),
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
