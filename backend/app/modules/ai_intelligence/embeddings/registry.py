"""Embedding Provider Registry for DocuMind AI (Phase 11)."""


from app.modules.ai_intelligence.embeddings.base import BaseEmbeddingProvider
from app.modules.ai_intelligence.embeddings.fast_embedder import fast_local_embedder
from app.modules.ai_intelligence.embeddings.gemini_embedder import GeminiEmbeddingProvider
from app.modules.ai_intelligence.embeddings.ollama_embedder import OllamaEmbeddingProvider


class EmbeddingRegistry:
    """Registry managing embedding providers with caching and fallback support."""

    def __init__(self) -> None:
        self._fast_embedder = fast_local_embedder
        self._providers: dict[str, BaseEmbeddingProvider] = {
            "sovereign": self._fast_embedder,
            "fast": self._fast_embedder,
            "local": self._fast_embedder,
        }

    def get_provider(
        self,
        provider_name: str = "sovereign",
        model: str | None = None,
        api_key: str | None = None,
        user_consent: bool = False,
        base_url: str | None = None,
    ) -> BaseEmbeddingProvider:
        key = (provider_name or "sovereign").lower().strip()
        if key in ("ollama",):
            return OllamaEmbeddingProvider(
                base_url=base_url or "http://localhost:11434",
                model=model or "nomic-embed-text",
            )
        if key in ("gemini", "google"):
            return GeminiEmbeddingProvider(
                api_key=api_key,
                model=model or "text-embedding-004",
                user_consent=user_consent,
            )
        return self._fast_embedder


embedding_registry = EmbeddingRegistry()
