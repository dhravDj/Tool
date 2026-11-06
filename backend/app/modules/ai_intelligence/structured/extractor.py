"""Structured Output Extractor with source-grounded citations (Phase 11)."""

import re
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    FileRecord,
    KnowledgeChunkRecord,
)
from app.modules.ai_intelligence.schemas.chat import Citation
from app.modules.ai_intelligence.schemas.knowledge import SourceReference
from app.modules.ai_intelligence.search.indexer import knowledge_indexer


class StructuredExtractor:
    """Extracts typed, validated JSON structures from indexed document chunks."""

    async def extract_schema(
        self,
        session: AsyncSession,
        file_id: uuid.UUID | str,
        target_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        f_uuid = uuid.UUID(str(file_id))

        await knowledge_indexer.index_file(session, f_uuid)

        chk_stmt = (
            select(KnowledgeChunkRecord, FileRecord)
            .join(FileRecord, KnowledgeChunkRecord.file_id == FileRecord.id)
            .where(KnowledgeChunkRecord.file_id == f_uuid)
            .order_by(KnowledgeChunkRecord.chunk_index)
        )
        res = await session.execute(chk_stmt)
        rows = res.all()

        if not rows:
            return {"error": "No indexed content found for file.", "extracted_data": {}, "citations": []}

        filename = rows[0][1].original_filename
        combined_text = "\n".join(r[0].content for r in rows[:10])

        fields = target_fields or ["title", "summary", "dates", "monetary_amounts", "entities"]
        extracted_data: dict[str, Any] = {}
        citations: list[Citation] = []

        # Deterministic extraction logic
        for field in fields:
            f_lower = field.lower().strip()
            if "date" in f_lower:
                dates = re.findall(r"\b(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b", combined_text)
                extracted_data[field] = list(set(dates))[:5]
            elif "money" in f_lower or "amount" in f_lower or "price" in f_lower or "revenue" in f_lower:
                amounts = re.findall(r"\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*(?:million|billion|thousand)\b", combined_text, re.IGNORECASE)
                extracted_data[field] = list(set(amounts))[:5]
            elif "title" in f_lower:
                extracted_data[field] = filename
            elif "summary" in f_lower:
                first_chk = rows[0][0].content.splitlines()
                extracted_data[field] = first_chk[0][:200] if first_chk else filename
            else:
                # General entity matching
                entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", combined_text)
                extracted_data[field] = list(set(entities))[:5]

        # Build citation from first chunk
        chk_0 = rows[0][0]
        src_ref_dict = chk_0.source_reference or {}
        src_ref = SourceReference.model_validate(src_ref_dict) if src_ref_dict else SourceReference(
            source_file_id=str(f_uuid),
            original_filename=filename,
            source_type=chk_0.source_type,
            formatted_citation=f"{filename} — Extracted Metadata",
        )
        cit = Citation(
            citation_id="[1]",
            file_id=str(f_uuid),
            filename=filename,
            source_type=chk_0.source_type,
            formatted_citation=src_ref.formatted_citation,
            snippet=chk_0.content[:240],
            page_number=src_ref.page_number,
            sheet_name=src_ref.sheet_name,
            cell_range=src_ref.cell_range,
            slide_number=src_ref.slide_number,
            line_start=src_ref.line_start,
            line_end=src_ref.line_end,
        )
        citations.append(cit)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "file_id": str(f_uuid),
            "filename": filename,
            "extracted_data": extracted_data,
            "citations": [c.model_dump() for c in citations],
            "duration_ms": round(duration_ms, 2),
        }


structured_extractor = StructuredExtractor()
