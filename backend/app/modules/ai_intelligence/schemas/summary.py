"""Summarization and Cross-File Intelligence Schemas (Phase 11)."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.ai_intelligence.schemas.chat import Citation


class SummaryRequest(BaseModel):
    """Request for single-file AI summarization."""

    file_id: str = Field(..., description="Target file UUID to summarize")
    summary_type: str = Field(
        default="detailed",
        description="short, detailed, executive, bullet, technical, section_wise, key_findings",
    )
    provider: str | None = Field(default=None, description="Provider override")
    allow_cloud: bool = Field(default=False, description="Cloud provider consent")


class SummaryResponse(BaseModel):
    """Generated document summary with citations."""

    summary_id: str = Field(..., description="Summary unique identifier")
    file_id: str = Field(..., description="Target file UUID")
    filename: str = Field(..., description="Target original filename")
    summary_type: str = Field(..., description="Requested summary style")
    summary_text: str = Field(..., description="Generated summary content")
    key_findings: list[str] = Field(default_factory=list, description="Bullet list of verified key takeaways")
    citations: list[Citation] = Field(default_factory=list, description="Source citations backing the summary")
    model_used: str = Field(..., description="Model version used")
    duration_ms: float = Field(..., description="Generation latency in ms")


class ComparisonRequest(BaseModel):
    """Request to compare 2 or more files and identify correlations or contradictions."""

    file_ids: list[str] = Field(..., min_length=2, max_length=20, description="List of file UUIDs to compare")
    aspects: list[str] | None = Field(default=None, description="Specific topics or metrics to compare (e.g. ['revenue', 'risks'])")
    provider: str | None = Field(default=None, description="Provider override")
    allow_cloud: bool = Field(default=False, description="Cloud provider consent")


class ComparisonResponse(BaseModel):
    """Multi-file comparison analysis with two-sided source citations."""

    comparison_id: str = Field(..., description="Comparison unique identifier")
    file_ids: list[str] = Field(..., description="Target file UUIDs evaluated")
    filenames: list[str] = Field(..., description="Target filenames")
    comparison_matrix: list[dict[str, Any]] = Field(default_factory=list, description="Structured feature-by-feature matrix")
    common_themes: list[str] = Field(default_factory=list, description="Agreements and common topics across files")
    differences: list[str] = Field(default_factory=list, description="Variations in context or figures")
    contradictions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Substantiated contradictions with exact citations from each conflicting side",
    )
    consolidated_summary: str = Field(..., description="Integrated executive synthesis")
    citations: list[Citation] = Field(default_factory=list, description="All citations from compared documents")
    model_used: str = Field(..., description="Model version used")
    duration_ms: float = Field(..., description="Generation latency in ms")
