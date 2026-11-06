"""Canonical schemas for Structured Data Intelligence Engine (Phase 9)."""

from typing import Any

from pydantic import BaseModel, Field


class ColumnStatistics(BaseModel):
    """Statistical summary of a single tabular column or field."""

    min_value: Any | None = Field(default=None)
    max_value: Any | None = Field(default=None)
    null_count: int = Field(default=0)
    distinct_count: int | None = Field(default=None)
    sample_values: list[Any] = Field(default_factory=list)


class ColumnProfile(BaseModel):
    """Detailed profile of a structured column or leaf property."""

    name: str = Field(..., description="Column or field property path")
    data_type: str = Field(default="string", description="Inferred or declared type (string, int, float, bool, timestamp, struct, list)")
    physical_type: str | None = Field(default=None, description="Physical storage type (e.g. INT64, BYTE_ARRAY, UTF8)")
    null_percentage: float = Field(default=0.0)
    is_unique: bool = Field(default=False)
    is_candidate_key: bool = Field(default=False)
    statistics: ColumnStatistics = Field(default_factory=ColumnStatistics)


class DataProfile(BaseModel):
    """Holistic dataset or document profile."""

    total_rows: int = Field(default=0, description="Total rows in dataset or root objects in collection")
    total_columns: int = Field(default=0, description="Total columns or top-level properties")
    candidate_keys: list[str] = Field(default_factory=list, description="Columns with unique non-null values suitable as primary keys")
    missing_cells_ratio: float = Field(default=0.0, description="Ratio of null/missing values across dataset")
    column_profiles: list[ColumnProfile] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Structural and syntax validation outcome."""

    is_valid: bool = Field(default=True)
    syntax_valid: bool = Field(default=True)
    duplicate_keys: list[str] = Field(default_factory=list, description="Detected duplicate keys in JSON/YAML mappings")
    schema_errors: list[str] = Field(default_factory=list)
    security_warnings: list[str] = Field(default_factory=list, description="Security findings e.g. XXE attempt, excessive aliases")


class RelationshipEdge(BaseModel):
    """Relationship or foreign-key edge connecting structured entities."""

    source_entity: str = Field(...)
    source_field: str = Field(...)
    target_entity: str = Field(...)
    target_field: str = Field(...)
    relationship_type: str = Field(default="foreign_key")
    confidence: float = Field(default=1.0)


class StructuredModelInfo(BaseModel):
    """Engine and parser metadata."""

    engine_name: str = Field(default="documind-structured-v1")
    format_parser: str = Field(default="native")
    is_bounded_memory: bool = Field(default=True)
    features_used: list[str] = Field(default_factory=list)


class StructuredDataDocument(BaseModel):
    """Canonical representation of an analyzed structured dataset or configuration file."""

    document_id: str = Field(..., description="Unique canonical document ID")
    source_file_id: str = Field(..., description="Associated file identifier")
    format: str = Field(..., description="Structured format: json, xml, yaml, toml, parquet")
    root_type: str = Field(default="object", description="Root entity structure: object, array, element, table")
    schema_definition: dict[str, Any] = Field(default_factory=dict, description="JSON Schema or Parquet schema representation")
    hierarchy: Any = Field(default_factory=dict, description="Normalized tree or nested dictionary/list hierarchy")
    records: list[dict[str, Any]] = Field(default_factory=list, description="Bounded sample of tabular records or rows (up to 100)")
    data_profile: DataProfile = Field(default_factory=DataProfile)
    validation_results: ValidationResult = Field(default_factory=ValidationResult)
    relationships: list[RelationshipEdge] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
    model_information: StructuredModelInfo = Field(default_factory=StructuredModelInfo)
    warnings: list[str] = Field(default_factory=list)
    status: str = Field(default="completed")
    raw_preview: str = Field(default="", description="Truncated raw text preview of the source payload")
