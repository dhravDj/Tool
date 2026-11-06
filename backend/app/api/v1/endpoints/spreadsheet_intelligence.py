"""Spreadsheet Intelligence API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import FileRecord, SpreadsheetAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.spreadsheet_intelligence.generators.parquet_exporter import (
    SpreadsheetParquetExporter,
)
from app.modules.spreadsheet_intelligence.pipeline import spreadsheet_pipeline
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetCapabilities,
    SpreadsheetDocument,
    SpreadsheetManifest,
)

router = APIRouter(tags=["Spreadsheet Intelligence"])


@router.get(
    "/spreadsheet-intelligence/capabilities",
    response_model=APIResponse[SpreadsheetCapabilities],
    summary="Get spreadsheet intelligence capabilities",
)
async def get_spreadsheet_capabilities() -> APIResponse[SpreadsheetCapabilities]:
    """Retrieve platform spreadsheet capabilities, supported formats, limits, and export formats."""
    caps = SpreadsheetCapabilities(
        supported_formats=spreadsheet_pipeline.list_supported_formats(),
        max_upload_size_mb=100,
        max_rows_limit=1_000_000,
        max_columns_limit=16_384,
        formula_extraction_supported=True,
        formula_execution_allowed=False,
        parquet_export_available=SpreadsheetParquetExporter.is_available(),
    )
    return APIResponse.ok(data=caps, message="Spreadsheet intelligence capabilities retrieved.")


@router.post(
    "/files/{file_id}/analyze-spreadsheet",
    response_model=APIResponse[SpreadsheetManifest],
    summary="Analyze a spreadsheet file",
    description="Parses multi-sheet structure, extracts formulas and cached results, profiles column data, and extracts tables/charts.",
)
async def analyze_spreadsheet_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[SpreadsheetManifest]:
    """Trigger spreadsheet intelligence pipeline for an ingested spreadsheet."""
    stmt = select(FileRecord).where(FileRecord.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    options = payload or {}

    try:
        _doc, manifest = await spreadsheet_pipeline.analyze_file_record(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spreadsheet analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Spreadsheet analysis completed with status: {manifest.status}",
    )


@router.get(
    "/files/{file_id}/spreadsheet-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get spreadsheet analysis record overview",
)
async def get_spreadsheet_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical spreadsheet analysis summary from PostgreSQL."""
    stmt = (
        select(SpreadsheetAnalysisRecord)
        .where(SpreadsheetAnalysisRecord.file_id == file_id)
        .order_by(desc(SpreadsheetAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No spreadsheet analysis records found for file '{file_id}'.",
        )

    data = {
        "id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "format": record.format,
        "sheet_count": record.sheet_count,
        "total_rows": record.total_rows,
        "total_columns": record.total_columns,
        "total_cells": record.total_cells,
        "formula_count": record.formula_count,
        "has_charts": record.has_charts,
        "has_tables": record.has_tables,
        "has_merged_cells": record.has_merged_cells,
        "has_hidden_sheets": record.has_hidden_sheets,
        "artifacts": record.artifacts,
        "workbook_metadata": record.workbook_metadata,
        "profiling_summary": record.profiling_summary,
        "warnings": record.warnings,
        "created_at": record.created_at.isoformat(),
    }
    return APIResponse.ok(data=data, message="Spreadsheet analysis record retrieved.")


@router.get(
    "/files/{file_id}/spreadsheet-analysis/result",
    response_model=APIResponse[SpreadsheetDocument],
    summary="Get complete canonical SpreadsheetDocument",
)
async def get_spreadsheet_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[SpreadsheetDocument]:
    """Retrieve the full canonical SpreadsheetDocument JSON representation from storage."""
    stmt = (
        select(SpreadsheetAnalysisRecord)
        .where(SpreadsheetAnalysisRecord.file_id == file_id)
        .order_by(desc(SpreadsheetAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record or "json" not in record.artifacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No canonical spreadsheet document found for file '{file_id}'.",
        )

    json_path = record.artifacts["json"]
    try:
        raw_bytes = await local_storage.read_file(json_path)
        doc_dict = json.loads(raw_bytes.decode("utf-8"))
        doc = SpreadsheetDocument(**doc_dict)
        return APIResponse.ok(data=doc, message="Spreadsheet document retrieved.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read spreadsheet document from storage: {e}",
        ) from e


@router.get(
    "/files/{file_id}/spreadsheet-analysis/worksheets",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List worksheets in workbook",
)
async def list_worksheets(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Retrieve list of worksheets with visibility and dimensions metadata."""
    res = await get_spreadsheet_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spreadsheet document for file '{file_id}' not found.",
        )

    sheets_list = []
    for ws in doc.worksheets:
        sheets_list.append({
            "sheet_id": ws.sheet_id,
            "name": ws.name,
            "position": ws.position,
            "visibility": ws.visibility.value,
            "dimensions": ws.dimensions,
            "total_rows": ws.total_rows,
            "total_columns": ws.total_columns,
            "has_merged_cells": len(ws.merged_ranges) > 0,
            "tables_count": len(ws.tables),
            "charts_count": len(ws.charts),
        })

    return APIResponse.ok(data=sheets_list, message="Worksheets catalog retrieved.")


@router.get(
    "/files/{file_id}/spreadsheet-analysis/worksheets/{sheet_id}",
    response_model=APIResponse[dict[str, Any]],
    summary="Get paginated worksheet data",
)
async def get_worksheet_data(
    file_id: uuid.UUID,
    sheet_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Rows per page"),
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve paginated rows and cells for a specific worksheet."""
    res = await get_spreadsheet_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spreadsheet document for file '{file_id}' not found.",
        )

    ws = next((w for w in doc.worksheets if w.sheet_id == sheet_id or w.name == sheet_id), None)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet '{sheet_id}' not found in document.",
        )

    # Paginate rows
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = ws.rows[start_idx:end_idx]

    data = {
        "sheet_id": ws.sheet_id,
        "name": ws.name,
        "position": ws.position,
        "visibility": ws.visibility.value,
        "dimensions": ws.dimensions,
        "total_rows": ws.total_rows,
        "total_columns": ws.total_columns,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (len(ws.rows) + page_size - 1) // page_size),
        "columns": [col.model_dump() for col in ws.columns],
        "rows": [row.model_dump() for row in page_rows],
        "merged_ranges": ws.merged_ranges,
        "tables": [t.model_dump() for t in ws.tables],
        "charts": [c.model_dump() for c in ws.charts],
        "profiling": ws.profiling.model_dump() if ws.profiling else None,
    }
    return APIResponse.ok(data=data, message=f"Worksheet '{ws.name}' page {page} retrieved.")


@router.get(
    "/files/{file_id}/spreadsheet-analysis/summary",
    response_model=APIResponse[dict[str, Any]],
    summary="Get spreadsheet intelligence summary",
)
async def get_spreadsheet_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve high-level overview, formulas catalog, and data quality insights."""
    res = await get_spreadsheet_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spreadsheet document for file '{file_id}' not found.",
        )

    formula_items = []
    for ws in doc.worksheets:
        for r in ws.rows:
            for c in r.cells:
                if c.formula:
                    formula_items.append({
                        "sheet": ws.name,
                        "cell": c.address,
                        "formula": c.formula,
                        "cached_value": c.cached_value,
                    })

    summary = {
        "document_id": doc.document_id,
        "file_id": doc.file_id,
        "workbook_metadata": doc.workbook_metadata.model_dump(),
        "sheet_count": len(doc.worksheets),
        "worksheets": [
            {
                "sheet_id": ws.sheet_id,
                "name": ws.name,
                "visibility": ws.visibility.value,
                "rows": ws.total_rows,
                "cols": ws.total_columns,
                "candidate_pks": ws.profiling.candidate_primary_keys if ws.profiling else [],
            }
            for ws in doc.worksheets
        ],
        "total_formulas": len(formula_items),
        "formulas_sample": formula_items[:20],
        "warnings": doc.warnings,
    }
    return APIResponse.ok(data=summary, message="Spreadsheet summary generated.")


@router.get(
    "/files/{file_id}/spreadsheet-analysis/manifest",
    response_model=APIResponse[SpreadsheetManifest],
    summary="Get execution manifest",
)
async def get_spreadsheet_manifest(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[SpreadsheetManifest]:
    """Retrieve operational manifest for spreadsheet intelligence processing."""
    stmt = (
        select(SpreadsheetAnalysisRecord)
        .where(SpreadsheetAnalysisRecord.file_id == file_id)
        .order_by(desc(SpreadsheetAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record or "manifest" not in record.artifacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No manifest found for file '{file_id}'.",
        )

    manifest_path = record.artifacts["manifest"]
    try:
        raw_bytes = await local_storage.read_file(manifest_path)
        manifest = SpreadsheetManifest(**json.loads(raw_bytes.decode("utf-8")))
        return APIResponse.ok(data=manifest, message="Spreadsheet manifest retrieved.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read manifest: {e}",
        ) from e


@router.get(
    "/files/{file_id}/spreadsheet-analysis/download",
    summary="Download spreadsheet artifacts",
)
async def download_spreadsheet_artifact(
    file_id: uuid.UUID,
    export_format: str = Query("json", alias="format", description="Format to download: json, markdown, csv, xlsx, parquet"),
    sheet_position: int = Query(1, description="Worksheet index for CSV export"),
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download exported artifact without exposing filesystem paths."""
    stmt = (
        select(SpreadsheetAnalysisRecord)
        .where(SpreadsheetAnalysisRecord.file_id == file_id)
        .order_by(desc(SpreadsheetAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis record found for file '{file_id}'.",
        )

    artifacts = record.artifacts
    fmt = export_format.lower().strip()

    artifact_key = None
    media_type = "application/octet-stream"
    filename = f"spreadsheet_{file_id}.{fmt}"

    if fmt == "json":
        artifact_key = artifacts.get("json")
        media_type = "application/json"
        filename = f"spreadsheet_{file_id}.json"
    elif fmt in ("markdown", "md"):
        artifact_key = artifacts.get("markdown")
        media_type = "text/markdown; charset=utf-8"
        filename = f"spreadsheet_{file_id}_report.md"
    elif fmt == "csv":
        artifact_key = artifacts.get(f"csv_sheet_{sheet_position}") or artifacts.get("csv_sheet_1")
        media_type = "text/csv; charset=utf-8"
        filename = f"spreadsheet_{file_id}_sheet_{sheet_position}.csv"
    elif fmt == "xlsx":
        artifact_key = artifacts.get("xlsx")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"spreadsheet_{file_id}_export.xlsx"
    elif fmt == "parquet":
        artifact_key = artifacts.get("parquet_sheet_1")
        media_type = "application/vnd.apache.parquet"
        filename = f"spreadsheet_{file_id}.parquet"

    if not artifact_key or not await local_storage.exists(artifact_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export format '{fmt}' not available for file '{file_id}'.",
        )

    file_bytes = await local_storage.read_file(artifact_key)
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
