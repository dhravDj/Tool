"""Master AI Intelligence Pipeline for DocuMind AI (Phase 11).

Central orchestration engine coordinating Universal Content Adapters, Modular Chunking,
Deterministic & Cloud Embeddings, BM25 + Cosine Hybrid Search, Sovereign RAG, Summarization,
and Cross-File Comparative Intelligence.
"""

import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_intelligence.cross_file import cross_file_comparator
from app.modules.ai_intelligence.rag import rag_pipeline
from app.modules.ai_intelligence.schemas.chat import ChatRequest, ChatResponse
from app.modules.ai_intelligence.schemas.provider import (
    CapabilitiesResponse,
    ModelInfo,
    ProviderInfo,
)
from app.modules.ai_intelligence.schemas.search import SearchQuery, SearchResult
from app.modules.ai_intelligence.schemas.summary import (
    ComparisonRequest,
    ComparisonResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.modules.ai_intelligence.search import hybrid_search_engine, knowledge_indexer
from app.modules.ai_intelligence.structured import structured_extractor
from app.modules.ai_intelligence.summarization import summarization_engine

logger = logging.getLogger(__name__)


class AIIntelligencePipeline:
    """Master universal AI orchestrator across all file modalities."""

    async def get_capabilities(self) -> CapabilitiesResponse:
        """Returns supported providers, embedding models, and multimodal capabilities."""
        sovereign_models = [
            ModelInfo(
                model_id="documind-sovereign-llm-v1",
                provider_name="sovereign",
                model_type="llm",
                display_name="DocuMind Sovereign LLM (Deterministic Grounded)",
                context_window=16384,
                max_output_tokens=4096,
                is_local=True,
                requires_api_key=False,
                capabilities=["chat", "rag", "summarization", "comparison", "structured_output"],
            ),
            ModelInfo(
                model_id="documind-fast-embed-384",
                provider_name="sovereign",
                model_type="embedding",
                display_name="DocuMind Fast Local Embedder (384-dim)",
                context_window=2048,
                max_output_tokens=0,
                is_local=True,
                requires_api_key=False,
                capabilities=["embedding", "semantic_search"],
            ),
        ]
        ollama_models = [
            ModelInfo(
                model_id="llama3.2",
                provider_name="ollama",
                model_type="llm",
                display_name="Llama 3.2 (Local Ollama)",
                context_window=8192,
                max_output_tokens=2048,
                is_local=True,
                requires_api_key=False,
                capabilities=["chat", "rag", "summarization"],
            ),
            ModelInfo(
                model_id="nomic-embed-text",
                provider_name="ollama",
                model_type="embedding",
                display_name="Nomic Embed Text (Ollama)",
                context_window=8192,
                max_output_tokens=0,
                is_local=True,
                requires_api_key=False,
                capabilities=["embedding", "semantic_search"],
            ),
        ]
        gemini_models = [
            ModelInfo(
                model_id="gemini-2.5-flash",
                provider_name="gemini",
                model_type="llm",
                display_name="Google Gemini 2.5 Flash",
                context_window=1048576,
                max_output_tokens=8192,
                is_local=False,
                requires_api_key=True,
                capabilities=["chat", "rag", "summarization", "comparison", "structured_output"],
            ),
            ModelInfo(
                model_id="text-embedding-004",
                provider_name="gemini",
                model_type="embedding",
                display_name="Google Text Embedding 004",
                context_window=2048,
                max_output_tokens=0,
                is_local=False,
                requires_api_key=True,
                capabilities=["embedding", "semantic_search"],
            ),
        ]

        providers = [
            ProviderInfo(
                provider_name="sovereign",
                display_name="DocuMind Sovereign AI (Local & Grounded)",
                is_available=True,
                is_local=True,
                requires_cloud_consent=False,
                models=sovereign_models,
            ),
            ProviderInfo(
                provider_name="ollama",
                display_name="Ollama Local Daemon",
                is_available=True,
                is_local=True,
                requires_cloud_consent=False,
                models=ollama_models,
            ),
            ProviderInfo(
                provider_name="gemini",
                display_name="Google Gemini Cloud",
                is_available=True,
                is_local=False,
                requires_cloud_consent=True,
                models=gemini_models,
            ),
        ]

        return CapabilitiesResponse(
            engine_version="11.0.0",
            supported_modalities=[
                "document", "spreadsheet", "presentation", "image",
                "audio", "video", "code", "structured_data", "archive"
            ],
            embedding_dimension=384,
            available_providers=providers,
            default_llm_model="documind-sovereign-llm-v1",
            default_embedding_model="documind-fast-embed-384",
            features=[
                "hybrid_search",
                "bm25_keyword_search",
                "cosine_vector_search",
                "reciprocal_rank_fusion",
                "zero_hallucination_citations",
                "multi_file_chat",
                "streaming_tokens",
                "cross_file_comparison",
                "contradiction_detection",
                "structured_output_extraction",
            ],
        )

    async def index_file(
        self,
        session: AsyncSession,
        file_id: uuid.UUID | str,
        force_reindex: bool = False,
    ) -> Any:
        return await knowledge_indexer.index_file(session, file_id, force_reindex=force_reindex)

    async def search(
        self,
        session: AsyncSession,
        query: SearchQuery,
    ) -> SearchResult:
        return await hybrid_search_engine.search(session, query)

    async def chat(
        self,
        session: AsyncSession,
        request: ChatRequest,
    ) -> ChatResponse:
        return await rag_pipeline.chat(session, request)

    async def chat_stream(
        self,
        session: AsyncSession,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        async for chunk in rag_pipeline.chat_stream(session, request):
            yield chunk

    async def summarize(
        self,
        session: AsyncSession,
        request: SummaryRequest,
        force_refresh: bool = False,
    ) -> SummaryResponse:
        return await summarization_engine.summarize(session, request, force_refresh=force_refresh)

    async def compare(
        self,
        session: AsyncSession,
        request: ComparisonRequest,
    ) -> ComparisonResponse:
        return await cross_file_comparator.compare(session, request)

    async def extract_structured(
        self,
        session: AsyncSession,
        file_id: uuid.UUID | str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return await structured_extractor.extract_schema(session, file_id, fields)


ai_intelligence_pipeline = AIIntelligencePipeline()
