"""Presentation Intelligence API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import FileRecord, PresentationAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.presentation_intelligence.pipeline import presentation_pipeline
from app.modules.presentation_intelligence.schemas.presentation_document import (
    PresentationCapabilities,
    PresentationDocument,
    PresentationManifest,
)

router = APIRouter(tags=["Presentation Intelligence"])


@router.get(
    "/presentation-intelligence/capabilities",
    response_model=APIResponse[PresentationCapabilities],
    summary="Get presentation intelligence capabilities",
)
async def get_presentation_capabilities() -> APIResponse[PresentationCapabilities]:
    """Retrieve platform presentation capabilities, supported formats, limits, and export formats."""
    caps = PresentationCapabilities(
        supported_formats=presentation_pipeline.list_supported_formats(),
        max_upload_size_mb=100,
        max_slides_limit=500,
        max_shapes_per_slide=2000,
        native_pptx_supported=True,
        native_odp_supported=True,
        legacy_ppt_supported=True,
        chart_extraction_supported=True,
        diagram_extraction_supported=True,
        speaker_notes_supported=True,
        image_intelligence_integration=True,
    )
    return APIResponse.ok(data=caps, message="Presentation intelligence capabilities retrieved.")


@router.post(
    "/files/{file_id}/analyze-presentation",
    response_model=APIResponse[PresentationManifest],
    summary="Analyze a presentation file",
    description="Parses slides, text runs, bullet hierarchy, tables, charts, images, diagrams, and speaker notes.",
)
async def analyze_presentation_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[PresentationManifest]:
    """Trigger presentation intelligence pipeline for an ingested presentation."""
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
        _doc, manifest = await presentation_pipeline.analyze_file_record(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Presentation analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Presentation analysis completed with status: {manifest.status}",
    )


@router.get(
    "/files/{file_id}/presentation-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get presentation analysis overview record",
)
async def get_presentation_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical presentation analysis summary from PostgreSQL."""
    stmt = (
        select(PresentationAnalysisRecord)
        .where(PresentationAnalysisRecord.file_id == file_id)
        .order_by(desc(PresentationAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No presentation analysis records found for file '{file_id}'.",
        )

    data = {
        "id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "format": record.format,
        "slide_count": record.slide_count,
        "hidden_slide_count": record.hidden_slide_count,
        "total_elements": record.total_elements,
        "has_notes": record.has_notes,
        "has_tables": record.has_tables,
        "has_charts": record.has_charts,
        "has_diagrams": record.has_diagrams,
        "has_images": record.has_images,
        "artifacts": record.artifacts,
        "presentation_metadata": record.presentation_metadata,
        "warnings": record.warnings,
        "engine_version": record.engine_version,
        "confidence": record.confidence,
        "processing_duration": record.processing_duration,
        "error_details": record.error_details,
        "created_at": record.created_at.isoformat(),
    }
    return APIResponse.ok(data=data, message="Presentation analysis record retrieved.")


@router.get(
    "/files/{file_id}/presentation-analysis/result",
    response_model=APIResponse[PresentationDocument],
    summary="Get complete canonical PresentationDocument",
)
async def get_presentation_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[PresentationDocument]:
    """Retrieve full canonical PresentationDocument JSON representation from storage."""
    stmt = (
        select(PresentationAnalysisRecord)
        .where(PresentationAnalysisRecord.file_id == file_id)
        .order_by(desc(PresentationAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record or "json" not in record.artifacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No canonical presentation document found for file '{file_id}'.",
        )

    json_key = record.artifacts["json"]
    try:
        raw_bytes = await local_storage.read_file(json_key)
        doc_dict = json.loads(raw_bytes.decode("utf-8"))
        doc = PresentationDocument.model_validate(doc_dict)
        return APIResponse.ok(data=doc, message="Canonical presentation document retrieved.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed reading canonical presentation document: {e}",
        ) from e


@router.get(
    "/files/{file_id}/presentation-analysis/slides",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="Get slides catalog list",
)
async def get_presentation_slides(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Retrieve list of slides with summary information."""
    res = await get_presentation_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation document for file '{file_id}' not found.",
        )

    slides_list = []
    for s in doc.slides:
        slides_list.append({
            "slide_id": s.slide_id,
            "slide_number": s.slide_number,
            "title": s.title,
            "elements_count": len(s.elements),
            "has_notes": bool(s.speaker_notes and s.speaker_notes.strip()),
            "hidden": s.hidden,
            "reading_order": s.reading_order,
        })

    return APIResponse.ok(data=slides_list, message="Presentation slides catalog retrieved.")


@router.get(
    "/files/{file_id}/presentation-analysis/slides/{slide_id}",
    response_model=APIResponse[dict[str, Any]],
    summary="Get detailed slide data",
)
async def get_slide_detail(
    file_id: uuid.UUID,
    slide_id: str,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve elements, tables, charts, and notes for a specific slide."""
    res = await get_presentation_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation document for file '{file_id}' not found.",
        )

    target_slide = next(
        (s for s in doc.slides if s.slide_id == slide_id or str(s.slide_number) == slide_id),
        None,
    )
    if not target_slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slide '{slide_id}' not found in presentation.",
        )

    # Correlate tables, charts, diagrams
    slide_tables = [
        t.model_dump()
        for t in doc.tables
        if t.slide_id == target_slide.slide_id or t.slide_number == target_slide.slide_number
    ]
    slide_charts = [
        c.model_dump()
        for c in doc.charts
        if c.slide_id == target_slide.slide_id or c.slide_number == target_slide.slide_number
    ]
    slide_diagrams = [
        d.model_dump()
        for d in doc.diagrams
        if d.slide_id == target_slide.slide_id or d.slide_number == target_slide.slide_number
    ]

    data = {
        "slide_id": target_slide.slide_id,
        "slide_number": target_slide.slide_number,
        "title": target_slide.title,
        "dimensions": target_slide.dimensions.model_dump() if target_slide.dimensions else None,
        "elements": [e.model_dump() for e in target_slide.elements],
        "tables": slide_tables,
        "charts": slide_charts,
        "diagrams": slide_diagrams,
        "speaker_notes": target_slide.speaker_notes,
        "hidden": target_slide.hidden,
        "reading_order": target_slide.reading_order,
    }
    return APIResponse.ok(data=data, message=f"Slide {target_slide.slide_number} data retrieved.")


@router.get(
    "/files/{file_id}/presentation-analysis/assets",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="Get presentation extracted assets",
)
async def get_presentation_assets(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Retrieve catalog of embedded images and media extracted from the presentation."""
    res = await get_presentation_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation document for file '{file_id}' not found.",
        )

    assets_data = [a.model_dump() for a in doc.assets]
    return APIResponse.ok(data=assets_data, message="Presentation assets catalog retrieved.")


@router.get(
    "/files/{file_id}/presentation-analysis/summary",
    response_model=APIResponse[dict[str, Any]],
    summary="Get presentation intelligence summary",
)
async def get_presentation_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve high-level presentation metrics, speaker notes overview, and structural findings."""
    res = await get_presentation_document_result(file_id=file_id, db=db)
    doc = res.data
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation document for file '{file_id}' not found.",
        )

    summary = {
        "document_id": doc.document_id,
        "file_id": doc.file_id,
        "metadata": doc.metadata.model_dump(),
        "dimensions": doc.presentation_dimensions.model_dump(),
        "slide_count": doc.slide_count,
        "hidden_slide_count": doc.metadata.hidden_slide_count,
        "total_elements": sum(len(s.elements) for s in doc.slides),
        "tables_count": len(doc.tables),
        "charts_count": len(doc.charts),
        "diagrams_count": len(doc.diagrams),
        "assets_count": len(doc.assets),
        "speaker_notes_count": len(doc.speaker_notes),
        "speaker_notes": [n.model_dump() for n in doc.speaker_notes],
        "warnings": doc.warnings,
        "extraction_metadata": doc.extraction_metadata,
        "confidence": doc.confidence,
    }
    return APIResponse.ok(data=summary, message="Presentation intelligence summary retrieved.")


@router.get(
    "/files/{file_id}/presentation-analysis/export/{export_format}",
    summary="Export presentation analysis artifact",
)
async def export_presentation_artifact(
    file_id: uuid.UUID,
    export_format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download exported artifact (json, markdown, txt, manifest)."""
    stmt = (
        select(PresentationAnalysisRecord)
        .where(PresentationAnalysisRecord.file_id == file_id)
        .order_by(desc(PresentationAnalysisRecord.created_at))
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
    filename = f"presentation_{file_id}.{fmt}"

    if fmt == "json":
        artifact_key = artifacts.get("json")
        media_type = "application/json"
        filename = f"presentation_{file_id}.json"
    elif fmt in ("markdown", "md"):
        artifact_key = artifacts.get("markdown")
        media_type = "text/markdown; charset=utf-8"
        filename = f"presentation_{file_id}_report.md"
    elif fmt in ("text", "txt"):
        artifact_key = artifacts.get("text")
        media_type = "text/plain; charset=utf-8"
        filename = f"presentation_{file_id}.txt"
    elif fmt == "manifest":
        artifact_key = artifacts.get("manifest")
        media_type = "application/json"
        filename = f"presentation_{file_id}_manifest.json"

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


@router.get(
    "/files/{file_id}/presentation-analysis/download",
    summary="Download presentation artifact via query param",
)
async def download_presentation_artifact(
    file_id: uuid.UUID,
    export_format: str = Query("json", alias="format", description="Format to download: json, markdown, text, manifest"),
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download exported artifact using query param format for frontend ease."""
    return await export_presentation_artifact(
        file_id=file_id,
        export_format=export_format,
        db=db,
    )
