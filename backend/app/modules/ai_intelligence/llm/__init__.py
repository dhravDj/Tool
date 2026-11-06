"""LLM Provider Architecture package for DocuMind AI (Phase 11)."""

from app.modules.ai_intelligence.llm.base import BaseLLMProvider
from app.modules.ai_intelligence.llm.gemini_llm import GeminiLLMProvider
from app.modules.ai_intelligence.llm.ollama_llm import OllamaLLMProvider
from app.modules.ai_intelligence.llm.router import ModelRouter, model_router
from app.modules.ai_intelligence.llm.sovereign_llm import (
    SovereignLLMProvider,
    sovereign_llm_provider,
)

__all__ = [
    "BaseLLMProvider",
    "SovereignLLMProvider",
    "sovereign_llm_provider",
    "OllamaLLMProvider",
    "GeminiLLMProvider",
    "ModelRouter",
    "model_router",
]
