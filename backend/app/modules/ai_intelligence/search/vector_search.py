"""Dense Semantic Vector Search using NumPy batch dot products."""

import uuid
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    EmbeddingRecord,
    FileRecord,
    KnowledgeChunkRecord,
)
from app.modules.ai_intelligence.schemas.knowledge import SourceReference
from app.modules.ai_intelligence.schemas.search import SearchFilter, SearchHit


class VectorSearchEngine:
    """Performs cosine similarity search over stored chunk embeddings."""

    async def search(
        self,
        session: AsyncSession,
        query_vector: list[float],
        top_k: int = 10,
        filters: SearchFilter | None = None,
    ) -> list[SearchHit]:
        if not query_vector:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 1e-9:
            q_vec = q_vec / q_norm

        # Build query for chunks that have embeddings
        stmt = (
            select(KnowledgeChunkRecord, EmbeddingRecord, FileRecord)
            .join(EmbeddingRecord, KnowledgeChunkRecord.id == EmbeddingRecord.chunk_id)
            .join(FileRecord, KnowledgeChunkRecord.file_id == FileRecord.id)
        )

        if filters:
            if filters.file_ids:
                f_uuids = [uuid.UUID(str(fid)) for fid in filters.file_ids]
                stmt = stmt.where(KnowledgeChunkRecord.file_id.in_(f_uuids))
            if filters.source_types:
                stmt = stmt.where(KnowledgeChunkRecord.source_type.in_(filters.source_types))

        res = await session.execute(stmt)
        rows = res.all()
        if not rows:
            return []

        candidates: list[dict[str, Any]] = []
        vectors: list[list[float]] = []

        for chunk_rec, emb_rec, file_rec in rows:
            v_data = emb_rec.vector_data
            if not v_data:
                continue
            vectors.append(v_data)
            candidates.append({
                "chunk": chunk_rec,
                "file": file_rec,
            })

        if not candidates:
            return []

        # Batch matrix cosine similarity
        mat = np.array(vectors, dtype=np.float32)
        # Row-normalize mat
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms < 1e-9] = 1.0
        norm_mat = mat / norms

        similarities = np.dot(norm_mat, q_vec)
        top_indices = np.argsort(-similarities)[:top_k]

        hits: list[SearchHit] = []
        for idx in top_indices:
            score = float(similarities[idx])
            cand = candidates[idx]
            chk: KnowledgeChunkRecord = cand["chunk"]
            fl: FileRecord = cand["file"]

            src_ref_data = chk.source_reference or {}
            src_ref = SourceReference.model_validate(src_ref_data) if src_ref_data else SourceReference(
                source_file_id=str(fl.id),
                original_filename=fl.original_filename,
                source_type=chk.source_type,
                formatted_citation=f"{fl.original_filename} — Chunk {chk.chunk_index + 1}",
            )

            hits.append(
                SearchHit(
                    chunk_id=chk.chunk_id,
                    file_id=str(chk.file_id),
                    filename=fl.original_filename,
                    source_type=chk.source_type,
                    content=chk.content,
                    source_reference=src_ref,
                    score=round(max(0.0, score), 4),
                    search_method="semantic",
                    highlight_snippet=chk.content[:240] + ("..." if len(chk.content) > 240 else ""),
                )
            )

        return hits


vector_search_engine = VectorSearchEngine()
