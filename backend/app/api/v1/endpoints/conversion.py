"""Universal File Conversion and Content Extraction API endpoints."""

import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.security import sanitize_filename
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import ConversionRecord
from app.modules.converters.schemas import (
    ConversionOptions,
    ConversionResponse,
    ConversionStatus,
    FormatCapabilities,
)
from app.modules.converters.service import UniversalConversionService

router = APIRouter(tags=["Universal File Converter"])
conversion_service = UniversalConversionService()


def _to_response_dto(rec: ConversionRecord) -> ConversionResponse:
    """Map SQLAlchemy ConversionRecord to Pydantic ConversionResponse DTO."""
    return ConversionResponse(
        id=str(rec.id),
        status=rec.status,
        original_filename=rec.original_filename,
        source_format=rec.source_format,
        target_format=rec.target_format,
        extraction_mode=rec.extraction_mode,
        progress_percent=rec.progress_percent,
        output_filename=rec.output_filename,
        output_size_bytes=rec.output_size_bytes,
        mime_type=rec.mime_type,
        preview_content=rec.preview_content or "",
        download_url=f"/api/v1/conversions/{rec.id}/download" if rec.status == "completed" else "",
        duration_seconds=rec.duration_seconds,
        warnings=rec.warnings or [],
        error_message=rec.error_message,
        created_at=rec.created_at.isoformat() if rec.created_at else "",
        completed_at=rec.completed_at.isoformat() if rec.completed_at else None,
    )


@router.get("/conversion/capabilities", response_model=APIResponse[list[FormatCapabilities]])
async def get_conversion_capabilities() -> APIResponse[list[FormatCapabilities]]:
    """Return capability matrix of all supported inputs and valid target formats."""
    caps = conversion_service.get_supported_capabilities()
    return APIResponse.ok(
        data=caps,
        message="Conversion capability matrix retrieved successfully.",
        meta={"total_formats": len(caps)},
    )


@router.post("/conversions", response_model=APIResponse[ConversionResponse])
async def convert_file(
    file: UploadFile = File(..., description="Source file to convert"),
    target_format: str = Form("txt", description="Target format: txt, md, json, csv, html, zip, srt, vtt"),
    extraction_mode: str = Form("structured_text", description="Extraction mode: plain_text, structured_text, complete"),
    ocr_enabled: bool = Form(True, description="Enable OCR for images and scanned documents"),
    preserve_tables: bool = Form(True, description="Preserve tabular structures"),
    preserve_headings: bool = Form(True, description="Preserve document section headers"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ConversionResponse]:
    """Upload a file, detect format, extract content, and convert to target format."""
    safe_name = sanitize_filename(file.filename or "uploaded_file")
    suffix = Path(safe_name).suffix

    options = ConversionOptions(
        ocr_enabled=ocr_enabled,
        preserve_tables=preserve_tables,
        preserve_headings=preserve_headings,
    )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        record = await conversion_service.convert_file(
            file_path=tmp_path,
            target_format=target_format,
            extraction_mode=extraction_mode,
            original_filename=safe_name,
            options=options,
            session=session,
        )
        return APIResponse.ok(
            data=_to_response_dto(record),
            message=f"File '{safe_name}' converted successfully to {target_format.upper()}.",
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/conversions/batch", response_model=APIResponse[list[ConversionResponse]])
async def convert_batch(
    files: list[UploadFile] = File(..., description="Batch of files to convert"),
    target_format: str = Form("txt", description="Target format"),
    extraction_mode: str = Form("structured_text", description="Extraction mode"),
    ocr_enabled: bool = Form(True, description="Enable OCR"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[ConversionResponse]]:
    """Convert multiple files in a single batch operation."""
    options = ConversionOptions(ocr_enabled=ocr_enabled)
    results: list[ConversionResponse] = []

    for file in files:
        safe_name = sanitize_filename(file.filename or "uploaded_file")
        suffix = Path(safe_name).suffix

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        try:
            record = await conversion_service.convert_file(
                file_path=tmp_path,
                target_format=target_format,
                extraction_mode=extraction_mode,
                original_filename=safe_name,
                options=options,
                session=session,
            )
            results.append(_to_response_dto(record))
        except Exception as e:
            # Record failed conversion response
            failed_resp = ConversionResponse(
                id=str(uuid.uuid4()),
                status=ConversionStatus.FAILED.value,
                original_filename=safe_name,
                source_format=suffix.lstrip("."),
                target_format=target_format,
                extraction_mode=extraction_mode,
                error_message=str(e),
                created_at=datetime.now(UTC).isoformat(),
            )
            results.append(failed_resp)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    return APIResponse.ok(
        data=results,
        message=f"Batch conversion completed for {len(results)} files.",
        meta={"total": len(results)},
    )


@router.get("/conversions/{conversion_id}", response_model=APIResponse[ConversionResponse])
async def get_conversion(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ConversionResponse]:
    """Retrieve conversion metadata, status, and preview."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")
    return APIResponse.ok(data=_to_response_dto(rec))


@router.get("/conversions/{conversion_id}/result")
async def get_conversion_result(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve direct extracted preview text and metadata."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")

    return {
        "conversion_id": str(rec.id),
        "status": rec.status,
        "output_filename": rec.output_filename,
        "mime_type": rec.mime_type,
        "preview_content": rec.preview_content,
        "warnings": rec.warnings,
        "duration_seconds": rec.duration_seconds,
    }


@router.get("/conversions/{conversion_id}/download")
async def download_converted_file(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Download converted output artifact with correct content disposition."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")

    file_path = Path(rec.output_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated artifact file not found.")

    return FileResponse(
        path=file_path,
        filename=rec.output_filename or file_path.name,
        media_type=rec.mime_type or "application/octet-stream",
    )


@router.get("/conversions/{conversion_id}/files", response_model=APIResponse[list[dict[str, Any]]])
async def list_conversion_files(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """List nested files contained in a complete bundle (Mode C) or archive."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")

    file_path = Path(rec.output_path)
    if not file_path.exists() or not zipfile.is_zipfile(file_path):
        return APIResponse.ok(
            data=[{"filename": rec.output_filename, "size_bytes": rec.output_size_bytes}],
            message="Single file conversion result.",
        )

    file_items: list[dict[str, Any]] = []
    with zipfile.ZipFile(file_path, "r") as zf:
        for info in zf.infolist():
            file_items.append(
                {
                    "filename": info.filename,
                    "size_bytes": info.file_size,
                    "compressed_size_bytes": info.compress_size,
                    "is_directory": info.is_dir(),
                }
            )

    return APIResponse.ok(data=file_items, message="Bundle file listing retrieved.")


@router.post("/conversions/{conversion_id}/retry", response_model=APIResponse[ConversionResponse])
async def retry_conversion(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ConversionResponse]:
    """Retry a failed or completed conversion."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")

    # Reset status
    rec.status = ConversionStatus.PROCESSING.value
    rec.error_message = None
    rec.progress_percent = 10.0
    await session.commit()
    await session.refresh(rec)

    return APIResponse.ok(data=_to_response_dto(rec), message="Conversion queued for retry.")


@router.delete("/conversions/{conversion_id}", response_model=APIResponse[dict[str, Any]])
async def delete_conversion(
    conversion_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Delete a conversion record and purge generated artifacts from disk."""
    stmt = select(ConversionRecord).where(ConversionRecord.id == conversion_id)
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found.")

    if rec.output_path and os.path.exists(rec.output_path):
        try:
            parent_dir = Path(rec.output_path).parent
            if parent_dir.name == str(conversion_id):
                shutil.rmtree(parent_dir, ignore_errors=True)
            else:
                os.remove(rec.output_path)
        except OSError:
            pass

    await session.delete(rec)
    await session.commit()

    return APIResponse.ok(
        data={"deleted_id": str(conversion_id)},
        message="Conversion record and artifacts deleted successfully.",
    )


@router.get("/conversion-history", response_model=APIResponse[list[ConversionResponse]])
async def list_conversion_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status (completed, failed, processing)"),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[ConversionResponse]]:
    """Retrieve paginated history of past file conversions."""
    query = select(ConversionRecord)
    if status:
        query = query.where(ConversionRecord.status == status)

    count_query = select(func.count(ConversionRecord.id))
    if status:
        count_query = count_query.where(ConversionRecord.status == status)

    total_count = (await session.execute(count_query)).scalar() or 0

    query = query.order_by(desc(ConversionRecord.created_at)).offset((page - 1) * limit).limit(limit)
    records = (await session.execute(query)).scalars().all()

    dtos = [_to_response_dto(r) for r in records]
    return APIResponse.ok(
        data=dtos,
        message="Conversion history retrieved successfully.",
        meta={
            "page": page,
            "limit": limit,
            "total": total_count,
            "total_pages": (total_count + limit - 1) // limit if limit else 1,
        },
    )
