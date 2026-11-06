"""Provider, Model, and Configuration Schemas for AI Intelligence (Phase 11)."""

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Metadata describing a supported LLM or embedding model."""

    model_id: str = Field(..., description="Unique model identifier (e.g. 'documind-sovereign-llm-v1')")
    provider_name: str = Field(..., description="Provider: sovereign, ollama, gemini, openai")
    model_type: str = Field(..., description="llm or embedding")
    display_name: str = Field(..., description="Human-readable model name")
    context_window: int = Field(default=8192, description="Maximum context window tokens")
    max_output_tokens: int = Field(default=2048, description="Maximum completion tokens")
    is_local: bool = Field(default=True, description="Runs fully on local host without network dependencies")
    requires_api_key: bool = Field(default=False, description="Requires external API key credentials")
    capabilities: list[str] = Field(default_factory=list, description="chat, rag, summarization, comparison, structured_output")


class ProviderInfo(BaseModel):
    """Runtime status of an LLM or embedding provider."""

    provider_name: str = Field(..., description="sovereign, ollama, gemini, openai")
    display_name: str = Field(..., description="Provider display name")
    is_available: bool = Field(default=True, description="Whether runtime/endpoint is reachable")
    is_local: bool = Field(default=True, description="True for local providers")
    requires_cloud_consent: bool = Field(default=False, description="Requires explicit cloud data transfer opt-in")
    models: list[ModelInfo] = Field(default_factory=list, description="List of models exposed by this provider")


class CapabilitiesResponse(BaseModel):
    """Platform-level AI intelligence capabilities response."""

    engine_version: str = Field(default="1.0.0", description="DocuMind AI engine version")
    supported_modalities: list[str] = Field(default_factory=list, description="Supported file types: documents, images, spreadsheets, presentations, audio, video, code, structured, archives")
    embedding_dimension: int = Field(default=384, description="Standard vector embedding dimension")
    available_providers: list[ProviderInfo] = Field(default_factory=list, description="Available providers")
    default_llm_model: str = Field(default="documind-sovereign-llm-v1")
    default_embedding_model: str = Field(default="documind-embed-v1")
    features: list[str] = Field(default_factory=list, description="Supported RAG features")


class AISettingsPayload(BaseModel):
    """User configuration updates for AI providers."""

    default_provider: str | None = Field(default=None, description="Preferred default provider")
    default_llm_model: str | None = Field(default=None, description="Preferred default model")
    cloud_consent_given: bool | None = Field(default=None, description="Cloud data transfer consent flag")
    ollama_base_url: str | None = Field(default=None, description="Ollama endpoint URL (e.g. 'http://localhost:11434')")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    chunk_size: int | None = Field(default=None, ge=100, le=2000, description="Chunk target tokens")
    chunk_overlap: int | None = Field(default=None, ge=0, le=500, description="Chunk overlap tokens")
