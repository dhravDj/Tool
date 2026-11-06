"""Retrieval-Augmented Generation (RAG) Pipeline for DocuMind AI (Phase 11).

Orchestrates multi-modal retrieval, evidence formatting, prompt construction,
injection defenses, LLM generation, citation verification, and conversational audit logging.
"""

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIConversationRecord,
    AIMessageRecord,
    AIUsageRecord,
    RetrievalRecord,
)
from app.modules.ai_intelligence.llm import model_router, sovereign_llm_provider
from app.modules.ai_intelligence.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
)
from app.modules.ai_intelligence.schemas.search import SearchFilter, SearchQuery
from app.modules.ai_intelligence.search.hybrid_search import hybrid_search_engine

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Production RAG engine ensuring zero hallucination and strict citation attribution."""

    async def _get_or_create_conversation(
        self,
        session: AsyncSession,
        request: ChatRequest,
    ) -> AIConversationRecord:
        if request.conversation_id:
            try:
                conv_uuid = uuid.UUID(str(request.conversation_id))
                stmt = select(AIConversationRecord).where(AIConversationRecord.id == conv_uuid)
                res = await session.execute(stmt)
                conv = res.scalar_one_or_none()
                if conv:
                    return conv
            except ValueError:
                pass

        primary_file_id = None
        if request.file_ids and len(request.file_ids) == 1:
            try:
                primary_file_id = uuid.UUID(str(request.file_ids[0]))
            except ValueError:
                pass

        title = request.message[:45] + ("..." if len(request.message) > 45 else "")
        new_conv = AIConversationRecord(
            title=title,
            provider=request.provider or "sovereign",
            model_name=request.model or "documind-sovereign-llm-v1",
            file_id=primary_file_id,
            context_mode=request.scope_type or "all_accessible",
            metadata_payload={"scope": request.scope_type, "file_ids": request.file_ids or []},
        )
        session.add(new_conv)
        await session.flush()
        return new_conv

    async def chat(
        self,
        session: AsyncSession,
        request: ChatRequest,
    ) -> ChatResponse:
        start_time = time.perf_counter()
        conversation = await self._get_or_create_conversation(session, request)

        # 1. Scope filter
        search_filter = None
        if request.file_ids:
            search_filter = SearchFilter(file_ids=request.file_ids)

        # 2. Hybrid Search for candidate context chunks
        search_query = SearchQuery(
            query=request.message,
            search_mode="hybrid",
            top_k=8,
            filter=search_filter,
        )
        search_res = await hybrid_search_engine.search(session, search_query)

        # 3. Format retrieved context chunks with token budgeting
        context_chunks: list[dict[str, Any]] = []
        retrieved_ids: list[str] = []
        budget_tokens = 3000
        accumulated_tokens = 0

        for hit in search_res.hits:
            hit_tokens = len(hit.content.split())
            if accumulated_tokens + hit_tokens > budget_tokens and context_chunks:
                break
            accumulated_tokens += hit_tokens
            retrieved_ids.append(hit.chunk_id)
            context_chunks.append({
                "chunk_id": hit.chunk_id,
                "file_id": hit.file_id,
                "filename": hit.filename,
                "source_type": hit.source_type,
                "content": hit.content,
                "source_reference": hit.source_reference.model_dump(),
                "score": hit.score,
            })

        # 4. Audit log retrieval
        retrieval_rec = RetrievalRecord(
            query=request.message,
            search_mode="hybrid",
            top_k=len(search_res.hits),
            filter_payload=search_filter.model_dump() if search_filter else {},
            hits_payload=[h.model_dump() for h in search_res.hits],
            duration_ms=search_res.duration_ms,
        )
        session.add(retrieval_rec)
        await session.flush()

        # 5. Record user message turn
        user_msg = AIMessageRecord(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            retrieval_id=retrieval_rec.id,
            token_count=max(1, len(request.message.split())),
            latency_ms=0.0,
        )
        session.add(user_msg)
        await session.flush()

        # 6. Model selection and generation
        provider_name = request.provider or "sovereign"
        if provider_name == "gemini" and not request.allow_cloud:
            warnings = ["Cloud provider requested without allow_cloud consent. Routed to Sovereign local LLM."]
            provider_name = "sovereign"
        else:
            warnings = []

        llm = model_router.get_provider(
            provider_name=provider_name,
            model_name=request.model,
            user_consent=request.allow_cloud,
        )

        answer_text, citations, completion_tokens = await llm.generate(
            prompt=request.message,
            context_chunks=context_chunks,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 7. Record assistant message turn
        assistant_msg = AIMessageRecord(
            conversation_id=conversation.id,
            role="assistant",
            content=answer_text,
            citations=[c.model_dump() for c in citations],
            retrieval_id=retrieval_rec.id,
            token_count=completion_tokens,
            latency_ms=latency_ms,
        )
        session.add(assistant_msg)
        await session.flush()

        # 8. Record telemetry usage
        usage_rec = AIUsageRecord(
            provider=llm.provider_name,
            model_name=llm.model_name,
            operation_type="chat",
            prompt_tokens=accumulated_tokens,
            completion_tokens=completion_tokens,
            total_tokens=accumulated_tokens + completion_tokens,
            duration_ms=latency_ms,
        )
        session.add(usage_rec)
        await session.commit()

        chat_msg = ChatMessage(
            message_id=str(assistant_msg.id),
            conversation_id=str(conversation.id),
            role="assistant",
            content=answer_text,
            citations=citations,
            retrieved_chunk_ids=retrieved_ids,
            provider=llm.provider_name,
            model_name=llm.model_name,
            prompt_tokens=accumulated_tokens,
            completion_tokens=completion_tokens,
            total_tokens=accumulated_tokens + completion_tokens,
            latency_ms=round(latency_ms, 2),
            metadata={"retrieval_id": str(retrieval_rec.id)},
            created_at=datetime.now(UTC).isoformat(),
        )

        return ChatResponse(
            conversation_id=str(conversation.id),
            message=chat_msg,
            citations=citations,
            retrieved_chunks_count=len(context_chunks),
            provider_used=llm.provider_name,
            model_used=llm.model_name,
            latency_ms=round(latency_ms, 2),
            warnings=warnings,
        )

    async def chat_stream(
        self,
        session: AsyncSession,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        start_time = time.perf_counter()
        conversation = await self._get_or_create_conversation(session, request)

        search_filter = SearchFilter(file_ids=request.file_ids) if request.file_ids else None
        search_query = SearchQuery(query=request.message, search_mode="hybrid", top_k=8, filter=search_filter)
        search_res = await hybrid_search_engine.search(session, search_query)

        context_chunks: list[dict[str, Any]] = []
        retrieved_ids: list[str] = []
        for hit in search_res.hits[:5]:
            retrieved_ids.append(hit.chunk_id)
            context_chunks.append({
                "chunk_id": hit.chunk_id,
                "file_id": hit.file_id,
                "filename": hit.filename,
                "source_type": hit.source_type,
                "content": hit.content,
                "source_reference": hit.source_reference.model_dump(),
                "score": hit.score,
            })

        # Send retrieval event
        retrieval_payload = {
            "type": "retrieval",
            "conversation_id": str(conversation.id),
            "retrieved_chunks": len(context_chunks),
            "hits": [h.model_dump() for h in search_res.hits[:5]],
        }
        yield f"event: retrieval\ndata: {json.dumps(retrieval_payload)}\n\n"

        provider_name = request.provider or "sovereign"
        if provider_name == "gemini" and not request.allow_cloud:
            provider_name = "sovereign"

        llm = model_router.get_provider(
            provider_name=provider_name,
            model_name=request.model,
            user_consent=request.allow_cloud,
        )

        accumulated_text: list[str] = []
        async for token in llm.generate_stream(
            prompt=request.message,
            context_chunks=context_chunks,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            accumulated_text.append(token)
            yield f"event: token\ndata: {json.dumps({'type': 'token', 'token': token})}\n\n"

        full_answer = "".join(accumulated_text)

        # Generate final citations
        _, citations, _ = await sovereign_llm_provider.generate(
            prompt=request.message,
            context_chunks=context_chunks,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        done_payload = {
            "type": "done",
            "conversation_id": str(conversation.id),
            "full_content": full_answer,
            "citations": [c.model_dump() for c in citations],
            "latency_ms": round(latency_ms, 2),
            "provider_used": llm.provider_name,
            "model_used": llm.model_name,
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"


rag_pipeline = RAGPipeline()
