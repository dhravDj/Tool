"""Chat and Conversation Schemas for Universal AI Intelligence (Phase 11)."""

from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Grounding citation linking an AI statement to its source artifact."""

    citation_id: str = Field(..., description="Unique citation marker ID (e.g. '[1]')")
    file_id: str = Field(..., description="UUID of source FileRecord")
    filename: str = Field(..., description="Basename of source file")
    source_type: str = Field(..., description="Modality category (document, spreadsheet, code, etc.)")
    formatted_citation: str = Field(..., description="Human-readable citation (e.g. 'sales.xlsx — Sheet: Q1, Cells B2:F12')")
    snippet: str = Field(..., description="Supporting verbatim text snippet from the chunk")
    page_number: int | None = Field(default=None, description="Page number")
    sheet_name: str | None = Field(default=None, description="Spreadsheet sheet name")
    cell_range: str | None = Field(default=None, description="Spreadsheet cell range")
    slide_number: int | None = Field(default=None, description="Presentation slide number")
    line_start: int | None = Field(default=None, description="Code start line")
    line_end: int | None = Field(default=None, description="Code end line")
    timestamp_start: float | None = Field(default=None, description="Audio/video start time")
    timestamp_end: float | None = Field(default=None, description="Audio/video end time")
    json_path: str | None = Field(default=None, description="JSON/XML path")
    archive_path: str | None = Field(default=None, description="Archive entry path")
    relevance_score: float = Field(default=1.0, description="Retrieval similarity or RRF score")


class ChatMessage(BaseModel):
    """A single turn within an AI conversation."""

    message_id: str = Field(..., description="UUID of the message")
    conversation_id: str = Field(..., description="UUID of the parent conversation")
    role: str = Field(..., description="user, assistant, or system")
    content: str = Field(..., description="Text content of the message")
    citations: list[Citation] = Field(default_factory=list, description="Verified source citations for assistant messages")
    retrieved_chunk_ids: list[str] = Field(default_factory=list, description="IDs of chunks retrieved for this turn")
    provider: str | None = Field(default=None, description="LLM provider name")
    model_name: str | None = Field(default=None, description="Model identifier")
    prompt_tokens: int | None = Field(default=None, description="Prompt token count")
    completion_tokens: int | None = Field(default=None, description="Completion token count")
    total_tokens: int | None = Field(default=None, description="Total tokens used")
    latency_ms: float | None = Field(default=None, description="Response generation latency in ms")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context or diagnostics")
    created_at: str = Field(..., description="ISO 8601 timestamp")


class ChatRequest(BaseModel):
    """User request for AI chat completion over files."""

    message: str = Field(..., min_length=1, max_length=10000, description="User question or prompt")
    conversation_id: str | None = Field(default=None, description="Existing conversation UUID to continue")
    scope_type: str = Field(
        default="all_accessible",
        description="Scope: single_file, selected_files, collection, archive, all_accessible",
    )
    file_ids: list[str] | None = Field(default=None, description="Specific file UUIDs when scope is single_file or selected_files")
    collection_id: str | None = Field(default=None, description="Collection UUID when scope is collection")
    provider: str | None = Field(default=None, description="Specific provider override: sovereign, ollama, gemini")
    model: str | None = Field(default=None, description="Specific model override")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Generation temperature")
    max_tokens: int = Field(default=2048, ge=64, le=8192, description="Maximum output tokens")
    allow_cloud: bool = Field(default=False, description="Explicit user consent to use cloud LLM providers")


class ChatResponse(BaseModel):
    """Response returned for a chat query."""

    conversation_id: str = Field(..., description="UUID of the active conversation")
    message: ChatMessage = Field(..., description="Assistant response message with citations")
    citations: list[Citation] = Field(default_factory=list, description="All supporting source references")
    retrieved_chunks_count: int = Field(default=0, description="Total candidate chunks retrieved")
    provider_used: str = Field(..., description="Provider selected by model router")
    model_used: str = Field(..., description="Model version utilized")
    latency_ms: float = Field(..., description="Turn-around latency in ms")
    warnings: list[str] = Field(default_factory=list, description="Advisory notices (e.g. insufficient context, truncation)")
