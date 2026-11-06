"""REST API endpoints for Structured Data Intelligence (Phase 9)."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import FileRecord, StructuredDataAnalysisRecord
from app.modules.structured_data_intelligence.pipeline import structured_pipeline
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    DataProfile,
    RelationshipEdge,
    StructuredDataDocument,
)

router = APIRouter(tags=["Structured Data Intelligence"])


@router.get(
    "/structured-data-intelligence/capabilities",
    response_model=APIResponse[dict[str, Any]],
    summary="Get structured data intelligence capabilities",
)
async def get_structured_capabilities() -> APIResponse[dict[str, Any]]:
    """Return supported structured data formats (JSON, XML, YAML, TOML, Parquet) and engines."""
    caps = structured_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Structured data intelligence capabilities retrieved.")


@router.get(
    "/structured-data-intelligence/supported-formats",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List supported structured data formats",
)
async def get_supported_formats() -> APIResponse[list[dict[str, Any]]]:
    """List all supported structured data formats and engine classes."""
    specs = structured_pipeline.engine_registry.list_supported_formats()
    return APIResponse.ok(data=specs, message="Supported structured data formats retrieved.")


@router.post(
    "/files/{file_id}/analyze-structured-data",
    response_model=APIResponse[dict[str, Any]],
    summary="Trigger structured data analysis",
)
async def analyze_structured_data_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Trigger structured data parsing, schema extraction, and column profiling."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    options = payload or {}
    try:
        doc = await structured_pipeline.process_and_persist(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Structured data analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data={
            "document_id": doc.document_id,
            "file_id": str(file_id),
            "format": doc.format,
            "root_type": doc.root_type,
            "status": doc.status,
            "total_rows": doc.data_profile.total_rows,
            "total_columns": doc.data_profile.total_columns,
            "candidate_keys": doc.data_profile.candidate_keys,
            "is_valid": doc.validation_results.is_valid,
        },
        message=f"Structured data analysis completed with status: {doc.status}",
    )


@router.get(
    "/files/{file_id}/structured-data-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get structured data analysis overview",
)
async def get_structured_data_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical structured data analysis summary record from PostgreSQL."""
    stmt = (
        select(StructuredDataAnalysisRecord)
        .where(StructuredDataAnalysisRecord.file_id == file_id)
        .order_by(desc(StructuredDataAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No structured data analysis found for file '{file_id}'.",
        )

    return APIResponse.ok(
        data={
            "id": str(record.id),
            "file_id": str(record.file_id),
            "status": record.status,
            "format": record.format,
            "root_type": record.root_type,
            "record_count": record.record_count,
            "field_count": record.field_count,
            "max_depth": record.max_depth,
            "is_valid": record.is_valid,
            "compression": record.compression,
            "model_name": record.model_name,
            "warnings": record.warnings,
            "artifacts": record.artifacts,
            "created_at": record.created_at.isoformat(),
        },
        message="Structured data analysis summary retrieved.",
    )


@router.get(
    "/files/{file_id}/structured-data-analysis/result",
    response_model=APIResponse[StructuredDataDocument],
    summary="Get full canonical StructuredDataDocument",
)
async def get_structured_data_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[StructuredDataDocument]:
    """Retrieve or generate full canonical StructuredDataDocument."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc, message="Canonical StructuredDataDocument retrieved.")


@router.get(
    "/files/{file_id}/structured-data-analysis/schema",
    response_model=APIResponse[dict[str, Any]],
    summary="Get inferred schema definition",
)
async def get_structured_data_schema(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve JSON Schema or Parquet schema definition."""
    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.schema_definition, message="Schema definition retrieved.")


@router.get(
    "/files/{file_id}/structured-data-analysis/profile",
    response_model=APIResponse[DataProfile],
    summary="Get dataset profile and column statistics",
)
async def get_structured_data_profile(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[DataProfile]:
    """Retrieve data profiling metrics, null ratios, and candidate keys."""
    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.data_profile, message="Data profile retrieved.")


@router.get(
    "/files/{file_id}/structured-data-analysis/relationships",
    response_model=APIResponse[list[RelationshipEdge]],
    summary="Get entity relationships",
)
async def get_structured_data_relationships(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[RelationshipEdge]]:
    """Retrieve inferred entity relationships or foreign keys."""
    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(data=doc.relationships, message="Relationships retrieved.")


@router.get(
    "/files/{file_id}/structured-data-analysis/records",
    response_model=APIResponse[dict[str, Any]],
    summary="Get sample records",
)
async def get_structured_data_records(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve sample tabular or object records."""
    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)
    return APIResponse.ok(
        data={"records": doc.records, "total_records": len(doc.records)},
        message="Sample records retrieved.",
    )


@router.get(
    "/files/{file_id}/structured-data-analysis/export/{format}",
    summary="Export structured data report",
)
async def export_structured_data_analysis(
    file_id: uuid.UUID,
    format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download exported structured data representation (json, markdown, csv)."""
    doc = await structured_pipeline.process_and_persist(file_id=file_id, session=db)

    fmt = format.lower().strip()
    if fmt == "json":
        data = structured_pipeline.json_generator.generate(doc)
        return Response(content=data, media_type="application/json")
    elif fmt in ("markdown", "md"):
        data = structured_pipeline.markdown_generator.generate(doc)
        return PlainTextResponse(content=data, media_type="text/markdown")
    elif fmt == "csv":
        data = structured_pipeline.csv_generator.generate(doc)
        return PlainTextResponse(content=data, media_type="text/csv")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Supported: json, markdown, csv.",
        )
