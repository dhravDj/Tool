"""Keyword Search Engine using BM25 and term-frequency ranking."""

import math
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    FileRecord,
    KnowledgeChunkRecord,
)
from app.modules.ai_intelligence.schemas.knowledge import SourceReference
from app.modules.ai_intelligence.schemas.search import SearchFilter, SearchHit


class KeywordSearchEngine:
    """Performs BM25 token-level full text search over stored knowledge chunks."""

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def _highlight(self, text: str, query_terms: set[str], snippet_len: int = 240) -> str:
        words = text.split()
        if not words:
            return ""

        # Find first occurrence of any query term
        match_idx = 0
        for i, w in enumerate(words):
            cleaned = re.sub(r"\W+", "", w.lower())
            if cleaned in query_terms:
                match_idx = i
                break

        start = max(0, match_idx - 15)
        end = min(len(words), start + 35)
        snippet_words = words[start:end]

        highlighted = []
        for w in snippet_words:
            cleaned = re.sub(r"\W+", "", w.lower())
            if cleaned in query_terms:
                highlighted.append(f"**{w}**")
            else:
                highlighted.append(w)

        res = " ".join(highlighted)
        if start > 0:
            res = "..." + res
        if end < len(words):
            res = res + "..."
        return res

    async def search(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 10,
        filters: SearchFilter | None = None,
    ) -> list[SearchHit]:
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        q_set = set(q_tokens)

        # Fetch candidate chunks
        stmt = (
            select(KnowledgeChunkRecord, FileRecord)
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

        doc_count = len(rows)
        # Precompute document lengths and doc frequencies of terms
        doc_tokens_list: list[list[str]] = []
        df: dict[str, int] = dict.fromkeys(q_set, 0)

        for chunk_rec, _ in rows:
            tokens = self._tokenize(chunk_rec.content)
            doc_tokens_list.append(tokens)
            chunk_token_set = set(tokens)
            for t in q_set:
                if t in chunk_token_set:
                    df[t] += 1

        avg_doc_len = (sum(len(d) for d in doc_tokens_list) / doc_count) if doc_count > 0 else 1.0

        # Calculate BM25 score for each document
        scored: list[tuple[float, KnowledgeChunkRecord, FileRecord, str]] = []

        for idx, (chunk_rec, file_rec) in enumerate(rows):
            tokens = doc_tokens_list[idx]
            d_len = len(tokens)
            if d_len == 0:
                continue

            tf_map: dict[str, int] = {}
            for t in tokens:
                if t in q_set:
                    tf_map[t] = tf_map.get(t, 0) + 1

            score = 0.0
            for t in q_set:
                f = tf_map.get(t, 0)
                if f > 0:
                    doc_freq = df.get(t, 0)
                    # Smoothed IDF
                    idf = math.log(1.0 + (doc_count - doc_freq + 0.5) / (doc_freq + 0.5))
                    term_score = idf * ((f * (self.k1 + 1.0)) / (f + self.k1 * (1.0 - self.b + self.b * (d_len / avg_doc_len))))
                    score += term_score

            if score > 0.0:
                snippet = self._highlight(chunk_rec.content, q_set)
                scored.append((score, chunk_rec, file_rec, snippet))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored[:top_k]

        hits: list[SearchHit] = []
        max_score = top_candidates[0][0] if top_candidates else 1.0
        if max_score <= 0.0:
            max_score = 1.0

        for sc, chk, fl, snip in top_candidates:
            src_ref_data = chk.source_reference or {}
            src_ref = SourceReference.model_validate(src_ref_data) if src_ref_data else SourceReference(
                source_file_id=str(fl.id),
                original_filename=fl.original_filename,
                source_type=chk.source_type,
                formatted_citation=f"{fl.original_filename} — Chunk {chk.chunk_index + 1}",
            )

            # Normalize BM25 score to (0.0, 1.0] range
            normalized_score = min(1.0, sc / max_score)

            hits.append(
                SearchHit(
                    chunk_id=chk.chunk_id,
                    file_id=str(chk.file_id),
                    filename=fl.original_filename,
                    source_type=chk.source_type,
                    content=chk.content,
                    source_reference=src_ref,
                    score=round(normalized_score, 4),
                    search_method="keyword",
                    highlight_snippet=snip,
                )
            )

        return hits


keyword_search_engine = KeywordSearchEngine()
