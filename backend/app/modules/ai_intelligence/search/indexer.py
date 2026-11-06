"""Knowledge Indexer for DocuMind AI (Phase 11).

Extracts, normalizes, chunks, embeds, and indexes any file modality into
KnowledgeDocumentRecord, KnowledgeChunkRecord, and EmbeddingRecord.
"""

import json
import logging
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    EmbeddingRecord,
    FileRecord,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
)
from app.infrastructure.storage.local import local_storage
from app.modules.ai_intelligence.adapters import content_adapter_registry
from app.modules.ai_intelligence.chunking import chunking_engine
from app.modules.ai_intelligence.embeddings import embedding_registry

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """Orchestrates document indexing, chunking, and embedding."""

    async def index_file(
        self,
        session: AsyncSession,
        file_id: uuid.UUID | str,
        embedder_name: str = "sovereign",
        force_reindex: bool = False,
    ) -> KnowledgeDocumentRecord:
        f_uuid = uuid.UUID(str(file_id))

        # 1. Load FileRecord with all potential intelligence analysis records
        stmt = (
            select(FileRecord)
            .where(FileRecord.id == f_uuid)
            .options(
                selectinload(FileRecord.extractions),
                selectinload(FileRecord.image_analyses),
                selectinload(FileRecord.spreadsheet_analyses),
                selectinload(FileRecord.presentation_analyses),
                selectinload(FileRecord.audio_analyses),
                selectinload(FileRecord.video_analyses),
                selectinload(FileRecord.code_analyses),
                selectinload(FileRecord.structured_data_analyses),
                selectinload(FileRecord.archive_analyses),
                selectinload(FileRecord.knowledge_documents),
            )
        )
        res = await session.execute(stmt)
        file_rec = res.scalar_one_or_none()
        if not file_rec:
            raise ValueError(f"File with ID {file_id} not found.")

        # Check if already indexed and not force_reindex
        if not force_reindex and file_rec.knowledge_documents:
            return file_rec.knowledge_documents[0]

        # 2. Extract best payload and determine source modality
        format_str = file_rec.extension or "txt"
        payload: dict[str, Any] = {}

        if file_rec.structured_data_analyses:
            rec = file_rec.structured_data_analyses[-1]
            format_str = rec.format
            payload = rec.artifacts or {}
            payload.setdefault("format", rec.format)
            payload.setdefault("root_type", rec.root_type)
        elif file_rec.code_analyses:
            rec = file_rec.code_analyses[-1]
            format_str = rec.language
            payload = rec.artifacts or {}
            payload.setdefault("language", rec.language)
            payload.setdefault("metrics", {"total_lines": rec.total_lines, "code_lines": rec.code_lines})
        elif file_rec.video_analyses:
            rec = file_rec.video_analyses[-1]
            format_str = rec.format
            payload = rec.artifacts or {}
            payload.setdefault("duration", rec.duration_seconds)
            payload.setdefault("format", rec.format)
        elif file_rec.audio_analyses:
            rec = file_rec.audio_analyses[-1]
            format_str = rec.format
            payload = rec.artifacts or {}
            payload.setdefault("duration_seconds", rec.duration_seconds)
            payload.setdefault("transcription_text", rec.transcription_text)
        elif file_rec.presentation_analyses:
            rec = file_rec.presentation_analyses[-1]
            format_str = rec.format
            payload = rec.artifacts or {}
        elif file_rec.spreadsheet_analyses:
            rec = file_rec.spreadsheet_analyses[-1]
            format_str = rec.format
            payload = rec.workbook_metadata or {}
        elif file_rec.image_analyses:
            rec = file_rec.image_analyses[-1]
            format_str = rec.format
            payload = rec.ocr_results or {}
        elif file_rec.archive_analyses:
            rec = file_rec.archive_analyses[-1]
            format_str = rec.archive_format
            payload = rec.artifacts or {}
            payload.setdefault("archive_format", rec.archive_format)
            payload.setdefault("total_entry_count", rec.entry_count)
        elif file_rec.extractions:
            rec = file_rec.extractions[-1]
            format_str = rec.output_format or file_rec.extension or "txt"
            payload = {}
            if rec.output_path and await local_storage.exists(rec.output_path):
                try:
                    raw_bytes = await local_storage.read_file(rec.output_path)
                    payload = json.loads(raw_bytes.decode("utf-8"))
                except Exception:
                    payload = {}
            if not payload and file_rec.storage_path and await local_storage.exists(file_rec.storage_path):
                try:
                    raw_bytes = await local_storage.read_file(file_rec.storage_path)
                    payload = {"text_content": raw_bytes.decode("utf-8", errors="replace")}
                except Exception:
                    payload = {}
            if not payload:
                payload = rec.record_metadata or {}
        else:
            # Fallback if no extraction or analysis record exists: read raw file if possible
            format_str = file_rec.extension or "txt"
            payload = {}
            if file_rec.storage_path and await local_storage.exists(file_rec.storage_path):
                try:
                    raw_bytes = await local_storage.read_file(file_rec.storage_path)
                    payload = {"text_content": raw_bytes.decode("utf-8", errors="replace")}
                except Exception:
                    payload = {}
            if not payload:
                payload = {
                    "text_content": f"File: {file_rec.original_filename}\nSize: {file_rec.file_size} bytes\nExtension: {file_rec.extension}"
                }

        # 3. Normalize into canonical KnowledgeDocument
        kdoc = content_adapter_registry.normalize(
            file_id=str(file_rec.id),
            filename=file_rec.original_filename,
            file_type_or_format=format_str,
            data=payload,
        )

        # 4. Remove previous knowledge document records if reindexing
        await session.execute(
            delete(KnowledgeDocumentRecord).where(KnowledgeDocumentRecord.file_id == f_uuid)
        )
        await session.flush()

        # 5. Insert KnowledgeDocumentRecord
        kdoc_rec = KnowledgeDocumentRecord(
            file_id=f_uuid,
            knowledge_document_id=kdoc.knowledge_document_id,
            source_type=kdoc.source_type,
            content_type=kdoc.content_type,
            title=kdoc.title,
            content_hash=kdoc.content_hash,
            extraction_status=kdoc.extraction_status,
            language=kdoc.language,
            total_blocks=len(kdoc.content_blocks),
            total_tokens=sum(b.token_estimate for b in kdoc.content_blocks),
            raw_metadata=kdoc.metadata,
        )
        session.add(kdoc_rec)
        await session.flush()

        # 6. Chunk Document
        chunks = chunking_engine.chunk_document(kdoc)
        if not chunks:
            # Create at least one fallback chunk
            chunks = [
                chunking_engine.chunk_document(
                    content_adapter_registry.normalize(
                        file_id=str(file_rec.id),
                        filename=file_rec.original_filename,
                        file_type_or_format="document",
                        data={"text_content": f"Document: {file_rec.original_filename}"},
                    )
                )[0]
            ]

        # 7. Embed chunks and save records
        embedder = embedding_registry.get_provider(embedder_name)
        chunk_texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(chunk_texts)

        for idx, (chk, emb_vec) in enumerate(zip(chunks, embeddings, strict=False)):
            chk_rec = KnowledgeChunkRecord(
                knowledge_document_id=kdoc_rec.id,
                file_id=f_uuid,
                chunk_id=chk.chunk_id,
                chunk_index=idx,
                content=chk.content,
                token_count=chk.token_count,
                source_type=kdoc.source_type,
                source_reference=chk.source_reference.model_dump(),
                content_hash=chk.content_hash,
                embedding_status="completed",
                metadata_payload=chk.metadata,
            )
            session.add(chk_rec)
            await session.flush()

            emb_rec = EmbeddingRecord(
                chunk_id=chk_rec.id,
                provider=embedder.provider_name,
                model_name=embedder.model_name,
                dimension=embedder.dimension,
                vector_data=emb_vec,
            )
            session.add(emb_rec)

        await session.commit()
        await session.refresh(kdoc_rec)
        return kdoc_rec


knowledge_indexer = KnowledgeIndexer()
