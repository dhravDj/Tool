"""Pydantic schemas for Universal AI Intelligence (Phase 11)."""

from app.modules.ai_intelligence.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Citation,
)
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeChunk,
    KnowledgeDocument,
    SourceReference,
)
from app.modules.ai_intelligence.schemas.provider import (
    AISettingsPayload,
    CapabilitiesResponse,
    ModelInfo,
    ProviderInfo,
)
from app.modules.ai_intelligence.schemas.search import (
    SearchFilter,
    SearchHit,
    SearchQuery,
    SearchResult,
)
from app.modules.ai_intelligence.schemas.summary import (
    ComparisonRequest,
    ComparisonResponse,
    SummaryRequest,
    SummaryResponse,
)

__all__ = [
    "SourceReference",
    "ContentBlock",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "Citation",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "SearchFilter",
    "SearchQuery",
    "SearchHit",
    "SearchResult",
    "SummaryRequest",
    "SummaryResponse",
    "ComparisonRequest",
    "ComparisonResponse",
    "ModelInfo",
    "ProviderInfo",
    "CapabilitiesResponse",
    "AISettingsPayload",
]
