"""Base Embedding Provider Interface for DocuMind AI (Phase 11)."""

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """Abstract interface for embedding generators."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'sovereign', 'ollama', 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific model (e.g. 'documind-fast-embed-384')."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Embeds a single text string into a normalized float vector."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embeds a batch of texts into normalized float vectors."""
        pass
