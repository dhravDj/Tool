"""Hybrid Search Engine combining Keyword BM25 and Dense Semantic Vectors via RRF."""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_intelligence.embeddings import embedding_registry
from app.modules.ai_intelligence.schemas.search import (
    SearchHit,
    SearchQuery,
    SearchResult,
)
from app.modules.ai_intelligence.search.keyword_search import keyword_search_engine
from app.modules.ai_intelligence.search.vector_search import vector_search_engine


class HybridSearchEngine:
    """Orchestrates Keyword BM25, Semantic Vector Search, and Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        rrf_k: int = 60,
        semantic_weight: float = 0.5,
        keyword_weight: float = 0.5,
    ) -> None:
        self.rrf_k = rrf_k
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    async def search(
        self,
        session: AsyncSession,
        query: SearchQuery,
        embedder_name: str = "sovereign",
    ) -> SearchResult:
        start_time = time.perf_counter()
        mode = (query.search_mode or "hybrid").lower().strip()
        top_k = query.top_k
        filters = query.filter

        if mode == "keyword":
            hits = await keyword_search_engine.search(
                session=session,
                query=query.query,
                top_k=top_k,
                filters=filters,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                query=query.query,
                search_mode="keyword",
                total_hits=len(hits),
                hits=hits,
                duration_ms=round(duration_ms, 2),
            )

        # For semantic or hybrid, compute query embedding
        embedder = embedding_registry.get_provider(embedder_name)
        query_vector = await embedder.embed_text(query.query)

        if mode == "semantic":
            hits = await vector_search_engine.search(
                session=session,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                query=query.query,
                search_mode="semantic",
                total_hits=len(hits),
                hits=hits,
                duration_ms=round(duration_ms, 2),
            )

        # Hybrid: retrieve larger candidate pool for both, then fuse with RRF
        candidate_k = max(top_k * 2, 20)
        kw_hits = await keyword_search_engine.search(
            session=session,
            query=query.query,
            top_k=candidate_k,
            filters=filters,
        )
        vec_hits = await vector_search_engine.search(
            session=session,
            query_vector=query_vector,
            top_k=candidate_k,
            filters=filters,
        )

        # Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = {}
        hit_map: dict[str, SearchHit] = {}

        # 1. Keyword rank contributions
        for rank, hit in enumerate(kw_hits, start=1):
            cid = hit.chunk_id
            hit_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.keyword_weight / (self.rrf_k + rank))

        # 2. Semantic rank contributions
        for rank, hit in enumerate(vec_hits, start=1):
            cid = hit.chunk_id
            if cid not in hit_map or hit.highlight_snippet:
                hit_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.semantic_weight / (self.rrf_k + rank))

        # Sort by RRF score descending
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_chunks = sorted_chunks[:top_k]

        max_rrf = sorted_chunks[0][1] if sorted_chunks else 1.0
        if max_rrf <= 0.0:
            max_rrf = 1.0

        fused_hits: list[SearchHit] = []
        for cid, rrf_sc in top_chunks:
            base_hit = hit_map[cid]
            # Normalize RRF score to 0.0-1.0 relative to highest hit
            normalized_score = min(1.0, rrf_sc / max_rrf)
            fused_hits.append(
                SearchHit(
                    chunk_id=base_hit.chunk_id,
                    file_id=base_hit.file_id,
                    filename=base_hit.filename,
                    source_type=base_hit.source_type,
                    content=base_hit.content,
                    source_reference=base_hit.source_reference,
                    score=round(normalized_score, 4),
                    search_method="hybrid",
                    highlight_snippet=base_hit.highlight_snippet,
                )
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            query=query.query,
            search_mode="hybrid",
            total_hits=len(fused_hits),
            hits=fused_hits,
            duration_ms=round(duration_ms, 2),
        )


hybrid_search_engine = HybridSearchEngine()
