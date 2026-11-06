"""Base LLM Provider Interface for DocuMind AI (Phase 11)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.modules.ai_intelligence.schemas.chat import Citation


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text generation and streaming."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name ('sovereign', 'ollama', 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> tuple[str, list[Citation], int]:
        """Generates response text, citations, and token count."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Streams response tokens."""
        pass
