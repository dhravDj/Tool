"""Search Schemas for Keyword, Semantic, and Hybrid Retrieval (Phase 11)."""

from pydantic import BaseModel, Field

from app.modules.ai_intelligence.schemas.knowledge import SourceReference


class SearchFilter(BaseModel):
    """Metadata filters applied before ranking."""

    file_ids: list[str] | None = Field(default=None, description="Subset of file UUIDs to query")
    source_types: list[str] | None = Field(default=None, description="Filter by format: document, spreadsheet, code, etc.")
    collection_id: str | None = Field(default=None, description="Filter by collection identifier")
    parent_archive_id: str | None = Field(default=None, description="Filter by ancestor archive UUID")
    date_from: str | None = Field(default=None, description="ISO date lower bound")
    date_to: str | None = Field(default=None, description="ISO date upper bound")


class SearchQuery(BaseModel):
    """Universal search request across all ingested file knowledge."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search terms or natural language question")
    search_mode: str = Field(default="hybrid", description="keyword, semantic, or hybrid")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of hits to return")
    filter: SearchFilter | None = Field(default=None, description="Optional metadata filter parameters")


class SearchHit(BaseModel):
    """A single retrieved knowledge chunk match."""

    chunk_id: str = Field(..., description="Unique chunk ID")
    file_id: str = Field(..., description="Source FileRecord UUID")
    filename: str = Field(..., description="Source original filename")
    source_type: str = Field(..., description="Modality category")
    content: str = Field(..., description="Chunk text content")
    source_reference: SourceReference = Field(..., description="Precise source locator")
    score: float = Field(..., description="Relevance score (RRF rank fusion or cosine similarity)")
    search_method: str = Field(..., description="Method that matched: hybrid, semantic, keyword")
    highlight_snippet: str | None = Field(default=None, description="Matching snippet with highlights")


class SearchResult(BaseModel):
    """Complete response returned by the search engine."""

    query: str = Field(..., description="Input search query")
    search_mode: str = Field(..., description="Search mode executed")
    total_hits: int = Field(..., description="Number of results found")
    hits: list[SearchHit] = Field(default_factory=list, description="Ranked list of matching hits")
    duration_ms: float = Field(..., description="Search execution latency in ms")
