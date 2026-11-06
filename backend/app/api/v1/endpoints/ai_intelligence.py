"""REST API endpoints for Universal AI Intelligence, RAG, and Search (Phase 11)."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import (
    AIConversationRecord,
    AIProviderConfigRecord,
    AIUsageRecord,
    FileRecord,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
)
from app.modules.ai_intelligence.pipeline import ai_intelligence_pipeline
from app.modules.ai_intelligence.schemas.chat import ChatRequest, ChatResponse
from app.modules.ai_intelligence.schemas.provider import (
    AISettingsPayload,
    CapabilitiesResponse,
)
from app.modules.ai_intelligence.schemas.search import SearchQuery, SearchResult
from app.modules.ai_intelligence.schemas.summary import (
    ComparisonRequest,
    ComparisonResponse,
    SummaryRequest,
    SummaryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


class IndexFileResponse(BaseModel):
    """Result of indexing a file into knowledge chunks."""

    file_id: str
    document_id: str
    source_type: str
    total_blocks: int
    total_chunks: int
    status: str


class IndexStatusResponse(BaseModel):
    """Indexing status of a specific file."""

    file_id: str
    is_indexed: bool
    document_id: str | None = None
    source_type: str | None = None
    chunk_count: int = 0
    token_count: int = 0
    content_hash: str | None = None


class ExtractStructuredRequest(BaseModel):
    """Payload to request structured entity extraction from a file."""

    file_id: str = Field(..., description="Target file UUID")
    fields: list[str] | None = Field(default=None, description="List of target fields to extract")


# 1. Platform Capabilities
@router.get("/capabilities", response_model=APIResponse[CapabilitiesResponse])
async def get_capabilities() -> APIResponse[CapabilitiesResponse]:
    """Returns AI capabilities, available models, local/cloud status, and supported modalities."""
    caps = await ai_intelligence_pipeline.get_capabilities()
    return APIResponse(data=caps)


# 2. Providers List
@router.get("/providers", response_model=APIResponse[list[dict[str, Any]]])
async def list_providers(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Returns available LLM and embedding providers with their current configuration status."""
    caps = await ai_intelligence_pipeline.get_capabilities()
    db_configs_res = await session.execute(select(AIProviderConfigRecord))
    db_configs = {c.provider_name: c for c in db_configs_res.scalars().all()}

    providers_data = []
    for prov in caps.available_providers:
        cfg = db_configs.get(prov.provider_name)
        providers_data.append({
            "provider_name": prov.provider_name,
            "display_name": prov.display_name,
            "is_available": prov.is_available,
            "is_local": prov.is_local,
            "requires_cloud_consent": prov.requires_cloud_consent,
            "user_consent_granted": cfg.user_consent_granted if cfg else False,
            "models": [m.model_dump() for m in prov.models],
        })
    return APIResponse(data=providers_data)


# 3. Index File
@router.post("/index/{file_id}", response_model=APIResponse[IndexFileResponse])
async def index_file(
    file_id: uuid.UUID,
    force: bool = Query(default=False, description="Force re-indexing even if already indexed"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[IndexFileResponse]:
    """Extracts, normalizes, chunks, embeds, and indexes a file into the knowledge base."""
    fl_res = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
    fl = fl_res.scalar_one_or_none()
    if not fl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")

    try:
        kdoc = await ai_intelligence_pipeline.index_file(session, file_id, force_reindex=force)
        # Count chunks
        chk_count_res = await session.execute(
            select(KnowledgeChunkRecord).where(KnowledgeChunkRecord.file_id == file_id)
        )
        chunk_count = len(chk_count_res.scalars().all())

        return APIResponse(
            data=IndexFileResponse(
                file_id=str(file_id),
                document_id=kdoc.knowledge_document_id,
                source_type=kdoc.source_type,
                total_blocks=kdoc.total_blocks,
                total_chunks=chunk_count,
                status="indexed",
            )
        )
    except Exception as e:
        logger.error(f"Failed to index file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        ) from e


# 4. Index Status
@router.get("/index/{file_id}/status", response_model=APIResponse[IndexStatusResponse])
async def get_index_status(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[IndexStatusResponse]:
    """Returns whether a file has been indexed, its document ID, and total chunks."""
    doc_res = await session.execute(
        select(KnowledgeDocumentRecord).where(KnowledgeDocumentRecord.file_id == file_id)
    )
    doc = doc_res.scalar_one_or_none()
    if not doc:
        return APIResponse(
            data=IndexStatusResponse(
                file_id=str(file_id),
                is_indexed=False,
            )
        )

    chk_res = await session.execute(
        select(KnowledgeChunkRecord).where(KnowledgeChunkRecord.file_id == file_id)
    )
    chunks = chk_res.scalars().all()

    return APIResponse(
        data=IndexStatusResponse(
            file_id=str(file_id),
            is_indexed=True,
            document_id=doc.knowledge_document_id,
            source_type=doc.source_type,
            chunk_count=len(chunks),
            token_count=doc.total_tokens,
            content_hash=doc.content_hash,
        )
    )


# 5. Hybrid Search
@router.post("/search", response_model=APIResponse[SearchResult])
async def search_knowledge(
    query: SearchQuery,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[SearchResult]:
    """Executes keyword, semantic, or hybrid search across indexed files with RRF ranking."""
    try:
        res = await ai_intelligence_pipeline.search(session, query)
        return APIResponse(data=res)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


# 6. RAG Chat
@router.post("/chat", response_model=APIResponse[ChatResponse])
async def chat_completion(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ChatResponse]:
    """Performs single-turn or multi-turn grounded RAG chat with exact citations."""
    try:
        res = await ai_intelligence_pipeline.chat(session, request)
        return APIResponse(data=res)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe)) from pe
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}",
        ) from e


# 7. RAG Chat Stream (SSE)
@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Streams RAG chat tokens and citation events via Server-Sent Events (SSE)."""
    return StreamingResponse(
        ai_intelligence_pipeline.chat_stream(session, request),
        media_type="text/event-stream",
    )


# 8. List Conversations
@router.get("/conversations", response_model=APIResponse[list[dict[str, Any]]])
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Returns list of recent AI conversations."""
    stmt = (
        select(AIConversationRecord)
        .order_by(desc(AIConversationRecord.updated_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    convs = res.scalars().all()
    data = [
        {
            "id": str(c.id),
            "title": c.title,
            "provider": c.provider,
            "model_name": c.model_name,
            "context_mode": c.context_mode,
            "file_id": str(c.file_id) if c.file_id else None,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in convs
    ]
    return APIResponse(data=data)


# 9. Get Conversation by ID
@router.get("/conversations/{conversation_id}", response_model=APIResponse[dict[str, Any]])
async def get_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Returns conversation metadata and ordered message history."""
    stmt = (
        select(AIConversationRecord)
        .where(AIConversationRecord.id == conversation_id)
        .options(selectinload(AIConversationRecord.messages))
    )
    res = await session.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "citations": m.citations or [],
            "token_count": m.token_count,
            "latency_ms": m.latency_ms,
            "created_at": m.created_at.isoformat(),
        }
        for m in conv.messages
    ]

    return APIResponse(
        data={
            "id": str(conv.id),
            "title": conv.title,
            "provider": conv.provider,
            "model_name": conv.model_name,
            "file_id": str(conv.file_id) if conv.file_id else None,
            "context_mode": conv.context_mode,
            "created_at": conv.created_at.isoformat(),
            "messages": messages,
        }
    )


# 10. Delete Conversation
@router.delete("/conversations/{conversation_id}", response_model=APIResponse[dict[str, str]])
async def delete_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, str]]:
    """Deletes an AI conversation session and associated message history."""
    stmt = select(AIConversationRecord).where(AIConversationRecord.id == conversation_id)
    res = await session.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    await session.delete(conv)
    await session.commit()
    return APIResponse(data={"deleted_id": str(conversation_id), "status": "deleted"})


# 11. Summarize
@router.post("/summarize", response_model=APIResponse[SummaryResponse])
async def summarize_file(
    request: SummaryRequest,
    refresh: bool = Query(default=False, description="Bypass cache and re-generate"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[SummaryResponse]:
    """Generates a structured, citation-backed summary of a single file."""
    try:
        res = await ai_intelligence_pipeline.summarize(session, request, force_refresh=refresh)
        return APIResponse(data=res)
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization error: {str(e)}",
        ) from e


# 12. Compare Files
@router.post("/compare", response_model=APIResponse[ComparisonResponse])
async def compare_files(
    request: ComparisonRequest,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ComparisonResponse]:
    """Compares multiple files, constructs comparison matrix, and detects contradictions."""
    try:
        res = await ai_intelligence_pipeline.compare(session, request)
        return APIResponse(data=res)
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison error: {str(e)}",
        ) from e


# 13. Extract Structured
@router.post("/extract-structured", response_model=APIResponse[dict[str, Any]])
async def extract_structured(
    request: ExtractStructuredRequest,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Extracts typed structured entities and metrics from a file with source citations."""
    try:
        res = await ai_intelligence_pipeline.extract_structured(session, request.file_id, request.fields)
        return APIResponse(data=res)
    except Exception as e:
        logger.error(f"Structured extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction error: {str(e)}",
        ) from e


# 14. Get Settings
@router.get("/settings", response_model=APIResponse[dict[str, Any]])
async def get_settings(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Returns AI configurations, privacy consent flags, and default model selection."""
    res = await session.execute(select(AIProviderConfigRecord))
    configs = res.scalars().all()
    cfg_map = {c.provider_name: c for c in configs}

    return APIResponse(
        data={
            "default_provider": "sovereign",
            "default_llm_model": "documind-sovereign-llm-v1",
            "cloud_consent_given": cfg_map.get("gemini").user_consent_granted if "gemini" in cfg_map else False,
            "ollama_base_url": cfg_map.get("ollama").base_url if "ollama" in cfg_map else "http://localhost:11434",
            "has_gemini_key": bool(cfg_map.get("gemini").api_key_encrypted) if "gemini" in cfg_map else False,
            "providers": [
                {
                    "provider_name": c.provider_name,
                    "is_enabled": c.is_enabled,
                    "default_model": c.default_model,
                    "user_consent_granted": c.user_consent_granted,
                }
                for c in configs
            ],
        }
    )


# 15. Update Settings
@router.put("/settings", response_model=APIResponse[dict[str, str]])
async def update_settings(
    payload: AISettingsPayload,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, str]]:
    """Updates AI provider credentials, cloud consent, and endpoint configurations."""
    if payload.cloud_consent_given is not None or payload.gemini_api_key is not None:
        gemini_stmt = select(AIProviderConfigRecord).where(AIProviderConfigRecord.provider_name == "gemini")
        g_res = await session.execute(gemini_stmt)
        g_cfg = g_res.scalar_one_or_none()
        if not g_cfg:
            g_cfg = AIProviderConfigRecord(
                provider_name="gemini",
                default_model="gemini-2.5-flash",
                is_enabled=True,
            )
            session.add(g_cfg)
        if payload.cloud_consent_given is not None:
            g_cfg.user_consent_granted = payload.cloud_consent_given
        if payload.gemini_api_key is not None:
            g_cfg.api_key_encrypted = payload.gemini_api_key

    if payload.ollama_base_url is not None:
        ollama_stmt = select(AIProviderConfigRecord).where(AIProviderConfigRecord.provider_name == "ollama")
        o_res = await session.execute(ollama_stmt)
        o_cfg = o_res.scalar_one_or_none()
        if not o_cfg:
            o_cfg = AIProviderConfigRecord(
                provider_name="ollama",
                default_model="llama3.2",
                is_enabled=True,
            )
            session.add(o_cfg)
        o_cfg.base_url = payload.ollama_base_url

    await session.commit()
    return APIResponse(data={"status": "settings_updated"})


# 16. Telemetry Usage
@router.get("/usage", response_model=APIResponse[dict[str, Any]])
async def get_usage_telemetry(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Returns AI token usage and latency telemetry across providers."""
    res = await session.execute(select(AIUsageRecord))
    records = res.scalars().all()

    total_tokens = sum(r.total_tokens for r in records)
    total_calls = len(records)
    avg_latency = (sum(r.duration_ms for r in records) / total_calls) if total_calls > 0 else 0.0

    by_provider: dict[str, int] = {}
    for r in records:
        by_provider[r.provider] = by_provider.get(r.provider, 0) + r.total_tokens

    return APIResponse(
        data={
            "total_tokens_used": total_tokens,
            "total_inference_calls": total_calls,
            "average_latency_ms": round(avg_latency, 2),
            "tokens_by_provider": by_provider,
        }
    )
