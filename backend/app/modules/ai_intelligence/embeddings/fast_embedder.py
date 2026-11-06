"""Fast Sovereign Local Embedder (Phase 11).

Deterministic, zero-dependency, normalized 384-dimensional dense vector generator.
Provides consistent semantic retrieval without external network calls or heavy model weights.
"""

import hashlib
import math
import re

from app.modules.ai_intelligence.embeddings.base import BaseEmbeddingProvider


class FastLocalEmbedder(BaseEmbeddingProvider):
    """High-speed deterministic 384-dim local embedder using subword n-gram hashing and L2 normalization."""

    def __init__(self, dimension: int = 384) -> None:
        self._dim = dimension

    @property
    def provider_name(self) -> str:
        return "sovereign"

    @property
    def model_name(self) -> str:
        return "documind-fast-embed-384"

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_token_to_indices(self, token: str) -> list[tuple[int, float]]:
        """Maps a token to deterministic index-weight pairs using SHA-256."""
        h = hashlib.sha256(token.encode("utf-8")).digest()
        results: list[tuple[int, float]] = []
        # Extract 4 bucket indices and signs from 32-byte digest
        for i in range(4):
            idx = int.from_bytes(h[i * 4 : i * 4 + 2], "big") % self._dim
            sign = 1.0 if (h[i * 4 + 2] % 2 == 0) else -1.0
            weight = (h[i * 4 + 3] / 255.0) * 0.5 + 0.5
            results.append((idx, sign * weight))
        return results

    def _compute_vector(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        if not text or not text.strip():
            return vec

        cleaned = text.lower().strip()
        words = re.findall(r"\w+", cleaned)
        if not words:
            return vec

        # 1. Word-level features with frequency damping
        word_freqs: dict[str, int] = {}
        for w in words:
            word_freqs[w] = word_freqs.get(w, 0) + 1

        for w, freq in word_freqs.items():
            tf = math.log1p(freq)
            for idx, weight in self._hash_token_to_indices(f"w:{w}"):
                vec[idx] += tf * weight

            # 2. Subword character 3-grams to 5-grams for morphological & multilingual matching
            padded = f"<{w}>"
            for n in (3, 4):
                if len(padded) >= n:
                    for i in range(len(padded) - n + 1):
                        ngram = padded[i : i + n]
                        for idx, weight in self._hash_token_to_indices(f"ng:{ngram}"):
                            vec[idx] += 0.3 * tf * weight

        # 3. L2 Unit Normalization
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-9:
            vec = [v / norm for v in vec]

        return vec

    async def embed_text(self, text: str) -> list[float]:
        return self._compute_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._compute_vector(t) for t in texts]


fast_local_embedder = FastLocalEmbedder()
