"""Document Extraction API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.config import settings
from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.canonical_document import (
    CanonicalDocument,
    ExtractionCapabilitiesResponse,
    ExtractionManifest,
    ExtractionRequest,
    ExtractionStatusResponse,
)
from app.infrastructure.database.models import ExtractionRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.extraction.ocr.router import OCRRouter
from app.modules.extraction.pipeline import extraction_pipeline

router = APIRouter(tags=["Document Content Extraction"])


@router.post(
    "/files/{file_id}/extract",
    response_model=APIResponse[ExtractionManifest],
    summary="Extract structured document content",
    description="Executes content extraction across supported document formats (PDF, DOCX, DOC, TXT, MD, RTF, ODT, EPUB).",
)
async def extract_document_content(
    file_id: uuid.UUID,
    payload: ExtractionRequest | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ExtractionManifest]:
    """Trigger synchronous extraction for an ingested file."""
    # Verify file exists
    stmt = select(FileRecord).where(FileRecord.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    options: dict[str, Any] = {}
    if payload:
        if payload.password:
            options["password"] = payload.password
        options["extract_images"] = payload.extract_images
        options.update(payload.options)

    try:
        _canonical_doc, manifest = await extraction_pipeline.extract_file_record(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document extraction failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Extraction completed with status: {manifest.errors and 'failed' or (manifest.warnings and 'completed_with_warnings' or 'completed')}",
    )


@router.get(
    "/files/{file_id}/extraction",
    response_model=APIResponse[ExtractionStatusResponse],
    summary="Get extraction status and artifact summary",
)
async def get_extraction_status(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ExtractionStatusResponse]:
    """Retrieve the latest extraction record and output file paths for a file."""
    stmt = (
        select(ExtractionRecord)
        .where(ExtractionRecord.file_id == file_id)
        .order_by(desc(ExtractionRecord.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extraction records found for file '{file_id}'.",
        )

    meta = record.record_metadata or {}
    manifest_dict = meta.get("manifest", {})

    status_resp = ExtractionStatusResponse(
        file_id=str(file_id),
        status=meta.get("extraction_status", "completed"),
        engine=record.engine,
        detected_format=manifest_dict.get("detected_format", "unknown"),
        page_count=meta.get("page_count", 0),
        block_count=meta.get("block_count", 0),
        scanned_pages=manifest_dict.get("scanned_page_count", 0),
        ocr_applied_pages=manifest_dict.get("ocr_page_count", 0),
        warnings=meta.get("warnings", []),
        errors=meta.get("errors", []),
        output_files=manifest_dict.get("output_files", {"canonical_json": record.output_path}),
        created_at=record.created_at.isoformat(),
    )

    return APIResponse.ok(data=status_resp)


@router.get(
    "/files/{file_id}/extraction/result",
    response_model=APIResponse[CanonicalDocument],
    summary="Get canonical document JSON",
)
async def get_canonical_document(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[CanonicalDocument]:
    """Return the full structured CanonicalDocument representation."""
    json_path = local_storage.get_local_path(f"processed/{file_id}/canonical_document.json")
    if not json_path or not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canonical document JSON not found for file '{file_id}'.",
        )

    try:
        content = json_path.read_text(encoding="utf-8")
        doc_data = json.loads(content)
        canonical_doc = CanonicalDocument.model_validate(doc_data)
        return APIResponse.ok(data=canonical_doc)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read canonical document: {exc}",
        ) from exc


@router.get(
    "/files/{file_id}/extraction/markdown",
    summary="Get generated Markdown text",
)
async def get_extracted_markdown(
    file_id: uuid.UUID,
    raw: bool = Query(default=False, description="Return raw text/markdown stream if true"),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Return the GitHub Flavored Markdown generated from extracted document structure."""
    md_path = local_storage.get_local_path(f"processed/{file_id}/document.md")
    if not md_path or not md_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted markdown not found for file '{file_id}'.",
        )

    markdown_text = md_path.read_text(encoding="utf-8")

    if raw:
        return PlainTextResponse(content=markdown_text, media_type="text/markdown")

    return APIResponse.ok(data={"file_id": str(file_id), "markdown": markdown_text})


@router.get(
    "/files/{file_id}/extraction/manifest",
    response_model=APIResponse[ExtractionManifest],
    summary="Get extraction manifest",
)
async def get_extraction_manifest(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[ExtractionManifest]:
    """Retrieve operational manifest containing execution timing, confidence and assets."""
    manifest_path = local_storage.get_local_path(f"processed/{file_id}/manifest.json")
    if not manifest_path or not manifest_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction manifest not found for file '{file_id}'.",
        )

    try:
        content = manifest_path.read_text(encoding="utf-8")
        manifest_data = json.loads(content)
        manifest = ExtractionManifest.model_validate(manifest_data)
        return APIResponse.ok(data=manifest)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read manifest: {exc}",
        ) from exc


@router.get(
    "/extraction/capabilities",
    response_model=APIResponse[ExtractionCapabilitiesResponse],
    summary="Get document extraction engine capabilities",
)
async def get_extraction_capabilities() -> APIResponse[ExtractionCapabilitiesResponse]:
    """List supported formats, engines, and OCR subsystem status."""
    ocr_router = OCRRouter()
    caps = ExtractionCapabilitiesResponse(
        supported_formats=extraction_pipeline.list_supported_formats(),
        engines=[
            "pymupdf_extractor",
            "docx_extractor",
            "legacy_doc_extractor",
            "plain_text_extractor",
            "markdown_extractor",
            "rtf_extractor",
            "odt_extractor",
            "epub_extractor",
        ],
        ocr_enabled=settings.OCR_ENABLED,
        ocr_engine=settings.OCR_ENGINE,
        ocr_available=ocr_router.is_ocr_available(),
    )
    return APIResponse.ok(data=caps)
