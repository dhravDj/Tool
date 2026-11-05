"""Sample mock AI provider plugin demonstrating AIProviderInterface compliance."""

from typing import Any

from app.plugins.interfaces.ai import (
    AIProviderInterface,
    CompletionRequest,
    CompletionResponse,
)
from app.plugins.interfaces.base import PluginMetadata, PluginType


class MockLocalAIProvider(AIProviderInterface):
    """Sample local AI provider verifying LLM/VLM interface contracts without heavy weights."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="mock_local_ai_provider",
            version="1.0.0",
            description="Phase 1 sample local AI provider for interface testing and verification.",
            plugin_type=PluginType.AI_PROVIDER,
            supported_formats=["*"],
            required_dependencies=[],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    @property
    def is_cloud(self) -> bool:
        return False

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        return True

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content=f"[Mock Local AI Summary for prompt: '{request.prompt[:50]}...']",
            model_used=request.model_name or "mock-local-v1",
            tokens_prompt=len(request.prompt.split()),
            tokens_completion=10,
            finish_reason="stop",
            raw_response={"mock": True},
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Return a fixed 16-dimensional dummy vector for testing
        return [[0.1] * 16 for _ in texts]
