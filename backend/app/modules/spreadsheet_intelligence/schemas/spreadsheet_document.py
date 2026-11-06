"""Canonical Pydantic v2 schemas for the Spreadsheet Intelligence Engine.

Represents full Excel workbooks, multi-sheet structures, cell data, formulas,
styling, merged ranges, tables, data profiling, and export manifests.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SheetVisibility(str, Enum):
    """Visibility state of a worksheet."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    VERY_HIDDEN = "very_hidden"


class CellDataType(str, Enum):
    """Inferred or explicit cell data type."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    FORMULA = "formula"
    EMPTY = "empty"
    ERROR = "error"


class CellStyle(BaseModel):
    """Visual style attributes of a spreadsheet cell."""

    model_config = ConfigDict(extra="ignore")

    font_name: str | None = None
    font_size: float | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    font_color: str | None = None
    fill_color: str | None = None
    horizontal_align: str | None = None
    vertical_align: str | None = None
    number_format: str | None = None
    has_border: bool = False


class CellData(BaseModel):
    """Atomic cell representation preserving values, formulas, and formatting."""

    model_config = ConfigDict(extra="ignore")

    address: str  # e.g. "A1", "C12"
    row: int  # 1-indexed row number
    column: int  # 1-indexed column number
    raw_value: Any = None
    formatted_value: str | None = None
    data_type: CellDataType = CellDataType.EMPTY
    formula: str | None = None
    cached_value: Any = None
    style: CellStyle | None = None
    hyperlink: str | None = None
    comment: str | None = None


class ColumnProfiling(BaseModel):
    """Statistical profiling and type inference for a worksheet column."""

    model_config = ConfigDict(extra="ignore")

    column_index: int
    column_letter: str
    column_name: str | None = None
    inferred_type: str = "text"
    total_count: int = 0
    null_count: int = 0
    unique_count: int = 0
    min_value: Any = None
    max_value: Any = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    is_candidate_key: bool = False
    frequent_values: list[dict[str, Any]] = Field(default_factory=list)


class ColumnData(BaseModel):
    """Metadata describing a sheet column."""

    model_config = ConfigDict(extra="ignore")

    column_index: int  # 1-indexed
    column_letter: str  # e.g. "A", "B", "AA"
    name: str | None = None
    width: float | None = None
    is_hidden: bool = False
    profiling: ColumnProfiling | None = None


class RowData(BaseModel):
    """Represents a row containing non-empty sparse cells."""

    model_config = ConfigDict(extra="ignore")

    row_index: int  # 1-indexed
    height: float | None = None
    is_hidden: bool = False
    cells: list[CellData] = Field(default_factory=list)


class TableMetadata(BaseModel):
    """Metadata for an embedded Excel Table object."""

    model_config = ConfigDict(extra="ignore")

    name: str
    display_name: str
    reference_range: str  # e.g. "A1:E20"
    columns: list[str] = Field(default_factory=list)
    has_totals_row: bool = False


class ChartMetadata(BaseModel):
    """Metadata for an embedded chart in a worksheet."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    chart_type: str = "unknown"
    data_range: str | None = None
    series_count: int = 0


class DataValidationMetadata(BaseModel):
    """Cell data validation rules."""

    model_config = ConfigDict(extra="ignore")

    validation_type: str
    formula1: str | None = None
    formula2: str | None = None
    ranges: list[str] = Field(default_factory=list)


class ConditionalFormatRule(BaseModel):
    """Conditional formatting rule definition."""

    model_config = ConfigDict(extra="ignore")

    rule_type: str
    priority: int = 0
    ranges: list[str] = Field(default_factory=list)
    formula: str | None = None


class WorksheetProfiling(BaseModel):
    """Summary data quality and structural findings for a worksheet."""

    model_config = ConfigDict(extra="ignore")

    total_rows: int = 0
    total_columns: int = 0
    populated_cells: int = 0
    empty_rows_count: int = 0
    duplicate_rows_count: int = 0
    candidate_primary_keys: list[str] = Field(default_factory=list)
    column_profiles: list[ColumnProfiling] = Field(default_factory=list)


class WorksheetData(BaseModel):
    """Canonical worksheet data container."""

    model_config = ConfigDict(extra="ignore")

    sheet_id: str
    name: str
    position: int
    visibility: SheetVisibility = SheetVisibility.VISIBLE
    dimensions: str | None = None  # e.g. "A1:Z100"
    total_rows: int = 0
    total_columns: int = 0
    merged_ranges: list[str] = Field(default_factory=list)
    columns: list[ColumnData] = Field(default_factory=list)
    rows: list[RowData] = Field(default_factory=list)
    tables: list[TableMetadata] = Field(default_factory=list)
    charts: list[ChartMetadata] = Field(default_factory=list)
    validations: list[DataValidationMetadata] = Field(default_factory=list)
    conditional_formats: list[ConditionalFormatRule] = Field(default_factory=list)
    profiling: WorksheetProfiling | None = None


class DefinedName(BaseModel):
    """Named range or formula expression defined in the workbook."""

    model_config = ConfigDict(extra="ignore")

    name: str
    value: str
    scope: str = "workbook"


class WorkbookMetadata(BaseModel):
    """Workbook-level administrative and technical metadata."""

    model_config = ConfigDict(extra="ignore")

    filename: str
    format: str
    creator: str | None = None
    last_modified_by: str | None = None
    created_at: str | None = None
    modified_at: str | None = None
    sheet_count: int = 1
    calculation_settings: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)


class SpreadsheetDocument(BaseModel):
    """Top-level canonical structured representation of an entire spreadsheet workbook."""

    model_config = ConfigDict(extra="ignore")

    document_id: str
    file_id: str
    schema_version: str = "1.0.0"
    workbook_metadata: WorkbookMetadata
    worksheets: list[WorksheetData] = Field(default_factory=list)
    defined_names: list[DefinedName] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SpreadsheetManifest(BaseModel):
    """Operational execution manifest recording runtime and exported artifact paths."""

    model_config = ConfigDict(extra="ignore")

    document_id: str
    file_id: str
    source_filename: str
    source_format: str
    status: str
    engine_name: str
    engine_version: str
    processing_time_seconds: float
    worksheet_count: int
    total_rows: int
    total_columns: int
    total_cells: int
    formula_count: int
    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SpreadsheetCapabilities(BaseModel):
    """Platform capabilities and limits for spreadsheet intelligence."""

    model_config = ConfigDict(extra="ignore")

    supported_formats: list[str] = ["xlsx", "xls", "csv", "tsv", "ods"]
    max_upload_size_mb: int = 100
    max_rows_limit: int = 1_000_000
    max_columns_limit: int = 16_384
    formula_extraction_supported: bool = True
    formula_execution_allowed: bool = False  # Strictly False for security
    parquet_export_available: bool = False
    supported_encodings: list[str] = ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin1"]
