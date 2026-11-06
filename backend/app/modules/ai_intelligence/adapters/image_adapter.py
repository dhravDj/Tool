"""Image Content Adapter (Phase 4: PNG, JPEG, WEBP, TIFF, BMP, GIF)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class ImageContentAdapter(BaseContentAdapter):
    """Adapts Phase 4 ImageDocument structures into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        img_dict = data.model_dump() if isinstance(data, BaseModel) else data

        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        full_text_parts: list[str] = []

        # 1. Visual Caption Block
        caption = img_dict.get("visual_caption") or img_dict.get("caption")
        if caption:
            full_text_parts.append(f"Visual Description: {caption}")
            caption_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="image",
                formatted_citation=f"{filename} — Visual Caption",
            )
            source_refs.append(caption_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"img_{file_id[:8]}_caption",
                    content=f"Visual Caption: {caption}",
                    block_type="image_caption",
                    source_reference=caption_ref,
                    token_estimate=max(1, len(caption.split())),
                )
            )

        # 2. OCR Text Blocks
        ocr_blocks = img_dict.get("ocr_blocks") or []
        for idx, o in enumerate(ocr_blocks):
            txt = (o.get("text") or "").strip()
            if not txt:
                continue
            full_text_parts.append(txt)
            bbox = o.get("bounding_box")
            citation_str = f"{filename} — OCR Region {idx + 1}"
            ocr_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="image",
                formatted_citation=citation_str,
                bounding_box=bbox,
            )
            source_refs.append(ocr_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"img_{file_id[:8]}_ocr_{idx}",
                    content=txt,
                    block_type="paragraph",
                    source_reference=ocr_ref,
                    token_estimate=max(1, len(txt.split())),
                    extraction_confidence=o.get("confidence"),
                    metadata={"bounding_box": bbox},
                )
            )

        # 3. Overall OCR Text fallback
        if not ocr_blocks and img_dict.get("ocr_text"):
            raw_ocr = img_dict.get("ocr_text", "").strip()
            if raw_ocr:
                full_text_parts.append(raw_ocr)
                ocr_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="image",
                    formatted_citation=f"{filename} — OCR Text",
                )
                source_refs.append(ocr_ref)
                content_blocks.append(
                    ContentBlock(
                        block_id=f"img_{file_id[:8]}_ocr_full",
                        content=raw_ocr,
                        block_type="paragraph",
                        source_reference=ocr_ref,
                        token_estimate=max(1, len(raw_ocr.split())),
                    )
                )

        # 4. Detected Objects / Diagrams / Charts
        detected = img_dict.get("detected_objects") or []
        if detected:
            obj_desc = "Detected Visual Elements: " + ", ".join(
                f"{d.get('label', 'element')} (conf: {d.get('confidence', 1.0):.2f})"
                for d in detected[:10]
            )
            full_text_parts.append(obj_desc)
            obj_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="image",
                formatted_citation=f"{filename} — Detected Objects",
            )
            source_refs.append(obj_ref)
            content_blocks.append(
                ContentBlock(
                    block_id=f"img_{file_id[:8]}_objects",
                    content=obj_desc,
                    block_type="structured_record",
                    source_reference=obj_ref,
                    token_estimate=max(1, len(obj_desc.split())),
                )
            )

        combined_text = "\n".join(full_text_parts) or f"Image file: {filename}"
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_img_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="image",
            content_type=img_dict.get("format", "image"),
            title=filename,
            content_blocks=content_blocks,
            metadata=img_dict.get("metadata", {}),
            source_references=source_refs,
            extraction_status="completed",
            language="en",
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
