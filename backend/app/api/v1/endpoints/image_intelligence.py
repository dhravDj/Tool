"""Image and Visual Intelligence API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import FileRecord, ImageAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.image_intelligence.pipeline import image_intelligence_pipeline
from app.modules.image_intelligence.schemas.image_document import (
    ImageAnalysisStatusResponse,
    ImageAskRequest,
    ImageAskResponse,
    ImageDocument,
    ImageManifest,
    VisionModelCapabilities,
)

router = APIRouter(tags=["Image & Visual Intelligence"])


@router.get(
    "/image-intelligence/capabilities",
    response_model=APIResponse[VisionModelCapabilities],
    summary="Get image intelligence capabilities",
)
async def get_image_intelligence_capabilities() -> APIResponse[VisionModelCapabilities]:
    """Retrieve platform vision capabilities, supported formats, preprocessing steps, and OCR readiness."""
    caps = image_intelligence_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Image intelligence capabilities retrieved.")


@router.post(
    "/files/{file_id}/analyze-image",
    response_model=APIResponse[ImageManifest],
    summary="Analyze an image file",
    description="Executes OCR, scene understanding, object detection, and diagram/chart parsing on supported image formats (PNG, JPEG, WEBP, TIFF, BMP, SVG).",
)
async def analyze_image_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ImageManifest]:
    """Trigger image intelligence pipeline for an ingested image."""
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
        _image_doc, manifest = await image_intelligence_pipeline.analyze_file_record(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Image analysis completed with status: {manifest.status}",
    )


@router.get(
    "/files/{file_id}/image-analysis",
    response_model=APIResponse[ImageAnalysisStatusResponse],
    summary="Get image analysis status and summary",
)
async def get_image_analysis_status(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ImageAnalysisStatusResponse]:
    """Retrieve the latest image intelligence record and artifact summary."""
    stmt = (
        select(ImageAnalysisRecord)
        .where(ImageAnalysisRecord.file_id == file_id)
        .order_by(desc(ImageAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image analysis records found for file '{file_id}'.",
        )

    manifest_obj: ImageManifest | None = None
    manifest_path = record.artifacts.get("image_manifest")
    if manifest_path and await local_storage.exists(manifest_path):
        try:
            m_bytes = await local_storage.read_file(manifest_path)
            manifest_obj = ImageManifest(**json.loads(m_bytes.decode("utf-8")))
        except Exception:
            pass

    status_resp = ImageAnalysisStatusResponse(
        file_id=str(file_id),
        status=record.status,
        format=record.format,
        width=record.width,
        height=record.height,
        color_mode=record.color_mode,
        ocr_word_count=record.ocr_word_count,
        detected_objects_count=record.detected_objects_count,
        has_charts=record.has_charts,
        has_diagrams=record.has_diagrams,
        artifacts=record.artifacts,
        manifest=manifest_obj,
    )

    return APIResponse.ok(data=status_resp)


@router.get(
    "/files/{file_id}/image-analysis/result",
    response_model=APIResponse[ImageDocument],
    summary="Get canonical image document JSON",
)
async def get_canonical_image_document(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ImageDocument]:
    """Retrieve the canonical ImageDocument JSON containing metadata, regions, and analyses."""
    stmt = (
        select(ImageAnalysisRecord)
        .where(ImageAnalysisRecord.file_id == file_id)
        .order_by(desc(ImageAnalysisRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image analysis record found for file '{file_id}'.",
        )

    json_path = record.artifacts.get("image_document_json")
    if not json_path or not await local_storage.exists(json_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canonical image document artifact not found in storage.",
        )

    content_bytes = await local_storage.read_file(json_path)
    doc_dict = json.loads(content_bytes.decode("utf-8"))
    canonical_doc = ImageDocument(**doc_dict)

    return APIResponse.ok(data=canonical_doc)


@router.post(
    "/files/{file_id}/ask-image",
    response_model=APIResponse[ImageAskResponse],
    summary="Ask a question about an analyzed image (VQA)",
)
async def ask_image_question(
    file_id: uuid.UUID,
    payload: ImageAskRequest,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ImageAskResponse]:
    """Ask a question about the image content, OCR text, diagrams, or charts."""
    try:
        response = await image_intelligence_pipeline.ask_image_question(
            file_id=file_id,
            question=payload.question,
            session=db,
        )
        return APIResponse.ok(data=response, message="Visual query processed successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Visual question answering failed: {exc}",
        ) from exc
