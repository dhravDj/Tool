"""REST API endpoints for Code Intelligence (Phase 9)."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import CodeAnalysisRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.code_intelligence.pipeline import code_pipeline
from app.modules.code_intelligence.schemas.code_document import (
    CodeDiagnostic,
    CodeDocument,
    CodeMetrics,
    CodeSymbol,
)

router = APIRouter(tags=["Code Intelligence"])


@router.get(
    "/code-intelligence/capabilities",
    response_model=APIResponse[dict[str, Any]],
    summary="Get code intelligence capabilities",
)
async def get_code_capabilities() -> APIResponse[dict[str, Any]]:
    """Return supported programming languages, AST parsers, and diagnostic features."""
    caps = code_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Code intelligence capabilities retrieved.")


@router.get(
    "/code-intelligence/supported-languages",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List supported programming languages",
)
async def get_supported_languages() -> APIResponse[list[dict[str, Any]]]:
    """List all 14 supported programming languages and associated extensions."""
    specs = code_pipeline.parser_registry.list_supported_languages()
    return APIResponse.ok(data=specs, message="Supported programming languages retrieved.")


@router.post(
    "/files/{file_id}/analyze-code",
    response_model=APIResponse[dict[str, Any]],
    summary="Trigger code analysis",
)
async def analyze_code_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Trigger static code parsing, symbol extraction, metrics, and diagnostics."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    options = payload or {}
    try:
        doc = await code_pipeline.process_and_persist(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data={
            "document_id": doc.document_id,
            "file_id": str(file_id),
            "language": doc.language,
            "status": doc.status,
            "metrics": doc.metrics.model_dump(),
            "symbols_count": len(doc.symbols),
            "diagnostics_count": len(doc.diagnostics),
        },
        message=f"Code analysis completed with status: {doc.status}",
    )


@router.get(
    "/files/{file_id}/code-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get code analysis overview",
)
async def get_code_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical code analysis summary record from PostgreSQL."""
    stmt = (
        select(CodeAnalysisRecord)
        .where(CodeAnalysisRecord.file_id == file_id)
        .order_by(desc(CodeAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No code analysis found for file '{file_id}'.",
        )

    return APIResponse.ok(
        data={
            "id": str(record.id),
            "file_id": str(record.file_id),
            "status": record.status,
            "language": record.language,
            "total_lines": record.total_lines,
            "code_lines": record.code_lines,
            "comment_lines": record.comment_lines,
            "blank_lines": record.blank_lines,
            "symbol_count": record.symbol_count,
            "function_count": record.function_count,
            "class_count": record.class_count,
            "import_count": record.import_count,
            "diagnostic_count": record.diagnostic_count,
            "has_syntax_errors": record.has_syntax_errors,
            "cyclomatic_complexity": record.cyclomatic_complexity,
            "model_name": record.model_name,
            "warnings": record.warnings,
            "artifacts": record.artifacts,
            "created_at": record.created_at.isoformat(),
        },
        message="Code analysis summary retrieved.",
    )


@router.get(
    "/files/{file_id}/code-analysis/result",
    response_model=APIResponse[CodeDocument],
    summary="Get full canonical CodeDocument",
)
async def get_code_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[CodeDocument]:
    """Retrieve or generate full canonical CodeDocument."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc, message="Canonical CodeDocument retrieved.")


@router.get(
    "/files/{file_id}/code-analysis/symbols",
    response_model=APIResponse[list[CodeSymbol]],
    summary="Get extracted code symbols",
)
async def get_code_symbols(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[CodeSymbol]]:
    """Retrieve all extracted functions, methods, classes, structs, and variables."""
    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.symbols, message="Code symbols retrieved.")


@router.get(
    "/files/{file_id}/code-analysis/dependencies",
    response_model=APIResponse[dict[str, Any]],
    summary="Get imports and dependencies",
)
async def get_code_dependencies(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve import statements and external package dependencies."""
    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(
        data={
            "imports": [i.model_dump() for i in doc.imports],
            "dependencies": [d.model_dump() for d in doc.dependencies],
        },
        message="Imports and dependencies retrieved.",
    )


@router.get(
    "/files/{file_id}/code-analysis/diagnostics",
    response_model=APIResponse[list[CodeDiagnostic]],
    summary="Get static code diagnostics",
)
async def get_code_diagnostics(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[CodeDiagnostic]]:
    """Retrieve syntax errors, linting warnings, and security findings."""
    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.diagnostics, message="Code diagnostics retrieved.")


@router.get(
    "/files/{file_id}/code-analysis/metrics",
    response_model=APIResponse[CodeMetrics],
    summary="Get code metrics",
)
async def get_code_metrics(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[CodeMetrics]:
    """Retrieve line counts, complexity, and nesting metrics."""
    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.metrics, message="Code metrics retrieved.")


@router.get(
    "/files/{file_id}/code-analysis/source",
    summary="Get raw source code content",
)
async def get_code_source(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    """Retrieve raw source code text of the analyzed file."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )
    content_bytes = await local_storage.read_file(file_record.storage_path)
    return PlainTextResponse(content=content_bytes.decode("utf-8", errors="replace"))


@router.get(
    "/files/{file_id}/code-analysis/export/{format}",
    summary="Export code analysis report",
)
async def export_code_analysis(
    file_id: uuid.UUID,
    format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download exported code analysis representation (json, markdown, text)."""
    doc = await code_pipeline.process_and_persist(file_id=file_id, session=db)

    fmt = format.lower().strip()
    if fmt == "json":
        data = code_pipeline.json_generator.generate(doc)
        return Response(content=data, media_type="application/json")
    elif fmt in ("markdown", "md"):
        data = code_pipeline.markdown_generator.generate(doc)
        return PlainTextResponse(content=data, media_type="text/markdown")
    elif fmt in ("text", "txt"):
        data = code_pipeline.text_generator.generate(doc)
        return PlainTextResponse(content=data, media_type="text/plain")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported code export format '{format}'. Supported: json, markdown, text.",
        )
