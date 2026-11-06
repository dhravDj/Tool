"""Cloud Gemini Embedding Provider with explicit privacy consent enforcement."""

import logging

import httpx

from app.modules.ai_intelligence.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini cloud embedding provider. Requires explicit user consent and API key."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-004",
        user_consent: bool = False,
        dimension: int = 768,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._user_consent = user_consent
        self._dim = dimension

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    def _verify_consent_and_key(self) -> None:
        if not self._user_consent:
            raise PermissionError(
                "Explicit user consent is required before transmitting file content or queries to cloud AI services."
            )
        if not self._api_key or not self._api_key.strip():
            raise ValueError("A valid Google Gemini API key is required.")

    async def embed_text(self, text: str) -> list[float]:
        self._verify_consent_and_key()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:embedContent?key={self._api_key}"
        payload = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                vec = data.get("embedding", {}).get("values", [])
                if vec and len(vec) != self._dim:
                    self._dim = len(vec)
                return vec
        except Exception as e:
            logger.error(f"Gemini embedding request failed: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            vec = await self.embed_text(text)
            results.append(vec)
        return results
