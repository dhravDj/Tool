"""Embedding Engine Package for DocuMind AI (Phase 11)."""

from app.modules.ai_intelligence.embeddings.base import BaseEmbeddingProvider
from app.modules.ai_intelligence.embeddings.fast_embedder import (
    FastLocalEmbedder,
    fast_local_embedder,
)
from app.modules.ai_intelligence.embeddings.gemini_embedder import GeminiEmbeddingProvider
from app.modules.ai_intelligence.embeddings.ollama_embedder import OllamaEmbeddingProvider
from app.modules.ai_intelligence.embeddings.registry import (
    EmbeddingRegistry,
    embedding_registry,
)

__all__ = [
    "BaseEmbeddingProvider",
    "FastLocalEmbedder",
    "fast_local_embedder",
    "OllamaEmbeddingProvider",
    "GeminiEmbeddingProvider",
    "EmbeddingRegistry",
    "embedding_registry",
]
