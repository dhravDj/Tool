"""Canonical schemas for Code Intelligence Engine (Phase 9)."""

from typing import Any

from pydantic import BaseModel, Field


class CodeSymbol(BaseModel):
    """Extracted code symbol (function, class, struct, method, interface, variable)."""

    symbol_id: str = Field(..., description="Unique symbol identifier")
    name: str = Field(..., description="Identifier name of the symbol")
    symbol_type: str = Field(..., description="Type: function, method, class, interface, struct, enum, variable, constant, property, module, namespace")
    start_line: int = Field(default=1, description="1-based start line")
    end_line: int = Field(default=1, description="1-based end line")
    parent_symbol: str | None = Field(default=None, description="Parent symbol ID if nested")
    visibility: str = Field(default="public", description="Visibility: public, protected, private, package")
    parameters: list[str] = Field(default_factory=list, description="Parameter signatures or names")
    return_type: str | None = Field(default=None, description="Inferred or explicit return type")
    documentation: str | None = Field(default=None, description="Extracted docstring or preceding comment")
    source_reference: str | None = Field(default=None, description="Short code snippet preview")


class CodeImport(BaseModel):
    """Import statement or include directive."""

    statement: str = Field(..., description="Raw import statement text")
    module_name: str = Field(..., description="Root or target module being imported")
    imported_symbols: list[str] = Field(default_factory=list, description="Explicit imported symbols or functions")
    is_relative: bool = Field(default=False, description="Whether this is a relative local import")
    is_external: bool = Field(default=True, description="Whether this targets a third-party/external dependency")
    alias: str | None = Field(default=None, description="As-alias name if defined")
    line_number: int = Field(default=1, description="Line number of the import statement")


class CodeDependency(BaseModel):
    """Project or package dependency entity."""

    name: str = Field(..., description="Dependency package name")
    version_spec: str | None = Field(default=None, description="Version constraint or specifier if declared")
    dependency_type: str = Field(default="external", description="Type: internal, external, dev, peer")
    is_resolved: bool = Field(default=True, description="Whether dependency is resolved")


class CodeMetrics(BaseModel):
    """Quantitative code metrics."""

    total_lines: int = Field(default=0)
    code_lines: int = Field(default=0)
    comment_lines: int = Field(default=0)
    blank_lines: int = Field(default=0)
    function_count: int = Field(default=0)
    class_count: int = Field(default=0)
    import_count: int = Field(default=0)
    avg_function_length: float = Field(default=0.0)
    max_function_length: int = Field(default=0)
    cyclomatic_complexity: float = Field(default=1.0)
    nesting_depth: int = Field(default=1)
    duplicate_code_candidates: list[str] = Field(default_factory=list)


class CodeDiagnostic(BaseModel):
    """Static analysis finding, syntax error, or security warning."""

    diagnostic_id: str = Field(..., description="Unique diagnostic ID")
    rule_id: str = Field(..., description="Rule or check identifier (e.g. SEC-001, SYNTAX-ERR)")
    severity: str = Field(default="warning", description="Severity: error, warning, info, hint")
    message: str = Field(..., description="Descriptive diagnostic finding")
    file_path: str = Field(default="", description="Path of target file")
    start_line: int = Field(default=1)
    end_line: int = Field(default=1)
    column: int = Field(default=1)
    tool_name: str = Field(default="documind-static-analyzer")
    evidence: str | None = Field(default=None, description="Offending code token or line snippet")
    suggested_remediation: str | None = Field(default=None, description="Remediation guidance")


class SyntaxValidationResult(BaseModel):
    """Syntax validation status."""

    is_valid: bool = Field(default=True)
    errors: list[str] = Field(default_factory=list)
    parser_used: str = Field(default="documind-ast-parser")


class CodeModelInfo(BaseModel):
    """Parser capability and engine metadata."""

    engine_name: str = Field(default="documind-code-v1")
    parser_type: str = Field(default="ast-heuristic")
    is_compiler: bool = Field(default=False)
    capabilities: list[str] = Field(default_factory=list)


class CodeDocument(BaseModel):
    """Canonical representation of an analyzed source code or database script."""

    document_id: str = Field(..., description="Unique canonical document ID")
    source_file_id: str = Field(..., description="Associated file identifier")
    language: str = Field(..., description="Programming language: py, js, ts, jsx, tsx, html, css, java, c, cpp, go, rs, php, sql")
    encoding: str = Field(default="utf-8")
    file_metadata: dict[str, Any] = Field(default_factory=dict)
    symbols: list[CodeSymbol] = Field(default_factory=list)
    imports: list[CodeImport] = Field(default_factory=list)
    dependencies: list[CodeDependency] = Field(default_factory=list)
    metrics: CodeMetrics = Field(default_factory=CodeMetrics)
    diagnostics: list[CodeDiagnostic] = Field(default_factory=list)
    syntax_validation: SyntaxValidationResult = Field(default_factory=SyntaxValidationResult)
    source_references: list[str] = Field(default_factory=list)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
    model_information: CodeModelInfo = Field(default_factory=CodeModelInfo)
    warnings: list[str] = Field(default_factory=list)
    status: str = Field(default="completed")
    source_code: str = Field(default="", description="Original source code text for viewer rendering")
