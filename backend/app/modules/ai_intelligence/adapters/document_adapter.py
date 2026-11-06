"""Document Content Adapter (Phase 3: PDF, DOCX, DOC, TXT, MD, RTF, ODT, EPUB)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class DocumentContentAdapter(BaseContentAdapter):
    """Adapts Phase 3 CanonicalDocument structures into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        doc_dict = data.model_dump() if isinstance(data, BaseModel) else data
        blocks_data = doc_dict.get("blocks", [])

        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        seen_citations: set[str] = set()
        full_text_parts: list[str] = []

        # If pages exist, extract block by block
        if blocks_data:
            for idx, b in enumerate(blocks_data):
                text = (b.get("text") or "").strip()
                if not text:
                    continue

                full_text_parts.append(text)
                page_num = b.get("page_number", 1)
                b_type = str(b.get("block_type") or "paragraph")
                if hasattr(b_type, "value"):
                    b_type = b_type.value

                citation_str = f"{filename} — Page {page_num}"
                bbox = b.get("bounding_box")

                src_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="document",
                    formatted_citation=citation_str,
                    page_number=page_num,
                    paragraph_index=idx,
                    bounding_box=bbox,
                )
                if citation_str not in seen_citations:
                    source_refs.append(src_ref)
                    seen_citations.add(citation_str)

                content_blocks.append(
                    ContentBlock(
                        block_id=f"doc_{file_id[:8]}_p{page_num}_b{idx}",
                        content=text,
                        block_type=b_type,
                        source_reference=src_ref,
                        token_estimate=max(1, len(text.split())),
                        extraction_confidence=b.get("confidence"),
                        metadata={"page": page_num, "engine": b.get("extraction_engine", "native")},
                    )
                )

        # Fallback if no blocks: check plain text
        if not content_blocks:
            raw_text = doc_dict.get("text_content") or doc_dict.get("text") or ""
            if raw_text:
                full_text_parts.append(raw_text)
                src_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="document",
                    formatted_citation=f"{filename} — Full Document",
                    page_number=1,
                )
                source_refs.append(src_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"doc_{file_id[:8]}_full",
                        content=raw_text,
                        block_type="paragraph",
                        source_reference=src_ref,
                        token_estimate=max(1, len(raw_text.split())),
                    )
                )

        combined_text = "\n".join(full_text_parts)
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_doc_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="document",
            content_type=doc_dict.get("detected_format", "document"),
            title=doc_dict.get("original_filename", filename),
            content_blocks=content_blocks,
            metadata=doc_dict.get("metadata", {}),
            source_references=source_refs,
            extraction_status=str(doc_dict.get("extraction_status", "completed")),
            language=doc_dict.get("metadata", {}).get("language", "en"),
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
