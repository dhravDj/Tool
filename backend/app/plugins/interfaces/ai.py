"""AI Provider plugin interface for local and cloud inference."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.plugins.interfaces.base import ProcessingPluginInterface


@dataclass
class CompletionRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    model_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResponse:
    content: str
    model_used: str
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    finish_reason: str = "stop"
    raw_response: dict[str, Any] | None = None


class AIProviderInterface(ProcessingPluginInterface):
    """Interface for local models (Ollama, vLLM, ONNX) and cloud APIs (Gemini, Anthropic, OpenAI)."""

    @property
    @abstractmethod
    def is_cloud(self) -> bool:
        """True if the provider transmits data to an external third-party cloud service."""
        pass

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate text completion from a prompt."""
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for input strings."""
        pass
