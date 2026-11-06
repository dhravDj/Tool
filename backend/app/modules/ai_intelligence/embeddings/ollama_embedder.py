"""Ollama Embedding Provider for DocuMind AI (Phase 11)."""

import logging

import httpx

from app.modules.ai_intelligence.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Local Ollama-backed embedding provider (e.g. nomic-embed-text, bge-m3)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        dimension: int = 768,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dim = dimension

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    async def is_available(self) -> bool:
        """Checks if local Ollama server is responding."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self._base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def embed_text(self, text: str) -> list[float]:
        url = f"{self._base_url}/api/embeddings"
        payload = {"model": self._model, "prompt": text}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                embedding = data.get("embedding", [])
                if embedding and len(embedding) != self._dim:
                    self._dim = len(embedding)
                return embedding
        except Exception as e:
            logger.warning(f"Ollama embedding failed for model {self._model}: {e}")
            raise RuntimeError(f"Ollama embedding error: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            vec = await self.embed_text(text)
            results.append(vec)
        return results
