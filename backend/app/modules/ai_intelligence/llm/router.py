"""Model Router for DocuMind AI (Phase 11)."""

from app.modules.ai_intelligence.llm.base import BaseLLMProvider
from app.modules.ai_intelligence.llm.gemini_llm import GeminiLLMProvider
from app.modules.ai_intelligence.llm.ollama_llm import OllamaLLMProvider
from app.modules.ai_intelligence.llm.sovereign_llm import (
    sovereign_llm_provider,
)


class ModelRouter:
    """Routes generation requests to Sovereign, Ollama, or Gemini providers."""

    def __init__(self) -> None:
        self._sovereign = sovereign_llm_provider

    def get_provider(
        self,
        provider_name: str = "sovereign",
        model_name: str | None = None,
        api_key: str | None = None,
        user_consent: bool = False,
        base_url: str | None = None,
    ) -> BaseLLMProvider:
        key = (provider_name or "sovereign").lower().strip()
        if key in ("ollama", "local_ollama"):
            return OllamaLLMProvider(
                base_url=base_url or "http://localhost:11434",
                model_name=model_name or "llama3.2",
            )
        if key in ("gemini", "google", "cloud"):
            return GeminiLLMProvider(
                api_key=api_key,
                model_name=model_name or "gemini-2.5-flash",
                user_consent=user_consent,
            )
        return self._sovereign


model_router = ModelRouter()
