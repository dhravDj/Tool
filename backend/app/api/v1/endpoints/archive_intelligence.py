"""REST API endpoints for Archive & Nested File Processing Engine (Phase 10)."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import (
    ArchiveAnalysisRecord,
    ArchiveEntryRecord,
    ArchiveRelationshipRecord,
    FileRecord,
)
from app.infrastructure.storage.local import local_storage
from app.modules.archive_intelligence.pipeline import archive_pipeline

router = APIRouter(tags=["Archive Intelligence"])


class AnalyzeArchiveRequest(BaseModel):
    """Payload to trigger archive analysis or extraction."""

    mode: str = Field(
        default="inspect_only",
        description="inspect_only, extract_only, extract_and_analyze, selective",
    )
    selected_entry_ids: list[str] | None = Field(
        default=None, description="Subset of entry IDs for selective mode"
    )
    password: str | None = Field(default=None, description="Optional archive decryption password")


class AnalyzeSelectedRequest(BaseModel):
    """Payload to extract and analyze specific entry IDs."""

    entry_ids: list[str] = Field(..., description="List of entry IDs to analyze")
    password: str | None = Field(default=None, description="Optional decryption password")


@router.get(
    "/archive-intelligence/capabilities",
    response_model=APIResponse[dict[str, Any]],
    summary="Get archive intelligence capabilities",
)
async def get_archive_capabilities() -> APIResponse[dict[str, Any]]:
    """Return supported archive formats, safety limits, and engine capabilities."""
    caps = archive_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Archive intelligence capabilities retrieved.")


@router.post(
    "/files/{file_id}/analyze-archive",
    response_model=APIResponse[dict[str, Any]],
    summary="Trigger archive inspection, extraction, or analysis",
)
async def analyze_archive_file(
    file_id: uuid.UUID,
    payload: AnalyzeArchiveRequest | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Inspect or extract archive, build directory hierarchy, and route child files."""
    file_record = await db.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found.",
        )

    mode = payload.mode if payload else "inspect_only"
    selected = payload.selected_entry_ids if payload else None
    pw = payload.password if payload else None

    try:
        doc = await archive_pipeline.process_and_persist(
            file_id=file_id,
            session=db,
            mode=mode,
            selected_entry_ids=selected,
            password=pw,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Archive processing failed: {e}",
        ) from e

    return APIResponse.ok(
        data=doc.model_dump(),
        message=f"Archive processed successfully in '{mode}' mode.",
    )


@router.get(
    "/files/{file_id}/archive-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get latest archive analysis record",
)
async def get_archive_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve the latest archive analysis record metadata for a given file."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive analysis found for file {file_id}.",
        )

    data = {
        "id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "archive_format": record.archive_format,
        "processing_mode": record.processing_mode,
        "entry_count": record.entry_count,
        "file_count": record.file_count,
        "directory_count": record.directory_count,
        "nested_archive_count": record.nested_archive_count,
        "total_uncompressed_size": record.total_uncompressed_size,
        "extracted_size": record.extracted_size,
        "compression_ratio": record.compression_ratio,
        "is_encrypted": record.is_encrypted,
        "is_corrupted": record.is_corrupted,
        "safety_report": record.safety_report,
        "artifacts": record.artifacts,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
    return APIResponse.ok(data=data, message="Archive analysis record retrieved.")


@router.get(
    "/files/{file_id}/archive-analysis/result",
    response_model=APIResponse[dict[str, Any]],
    summary="Get full canonical ArchiveDocument result",
)
async def get_archive_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve full canonical ArchiveDocument representation from saved artifacts."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive analysis found for file {file_id}.",
        )

    json_path = record.artifacts.get("json")
    if json_path:
        local_p = local_storage.get_local_path(json_path)
        if local_p and local_p.exists():
            with open(local_p, encoding="utf-8") as f:
                doc_dict = json.load(f)
            return APIResponse.ok(data=doc_dict, message="Full archive document retrieved.")

    # Reconstruct from record if artifact missing
    return APIResponse.ok(
        data={
            "archive_id": str(record.id),
            "source_file_id": str(record.file_id),
            "archive_format": record.archive_format,
            "status": record.status,
            "metadata": record.archive_metadata,
            "safety_report": record.safety_report,
        },
        message="Archive document retrieved from record.",
    )


@router.get(
    "/files/{file_id}/archive-analysis/summary",
    response_model=APIResponse[dict[str, Any]],
    summary="Get high-level summary of archive analysis",
)
async def get_archive_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Return high-level summary metrics of archive."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive analysis found for file {file_id}.",
        )

    summary = {
        "archive_id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "format": record.archive_format,
        "entry_count": record.entry_count,
        "file_count": record.file_count,
        "directory_count": record.directory_count,
        "nested_archive_count": record.nested_archive_count,
        "total_uncompressed_bytes": record.total_uncompressed_size,
        "extracted_bytes": record.extracted_size,
        "compression_ratio": record.compression_ratio,
        "is_encrypted": record.is_encrypted,
        "is_corrupted": record.is_corrupted,
        "safety_violations": record.safety_report.get("blocked_entry_count", 0),
        "duration_seconds": record.processing_duration,
    }
    return APIResponse.ok(data=summary, message="Archive summary retrieved.")


@router.get(
    "/files/{file_id}/archive-analysis/entries",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List paginated archive entries",
)
async def get_archive_entries(
    file_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entry_type: str | None = Query(None, description="file, directory, symlink"),
    search: str | None = Query(None, description="Filter by filename"),
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """List paginated archive entries with optional filtering by type or filename."""
    stmt_rec = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res_rec = await db.execute(stmt_rec)
    analysis = res_rec.scalars().first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive analysis found for file {file_id}.",
        )

    stmt = select(ArchiveEntryRecord).where(ArchiveEntryRecord.archive_analysis_id == analysis.id)
    if entry_type:
        stmt = stmt.where(ArchiveEntryRecord.entry_type == entry_type)
    if search:
        stmt = stmt.where(ArchiveEntryRecord.filename.ilike(f"%{search}%"))

    stmt = stmt.offset(skip).limit(limit)
    res_entries = await db.execute(stmt)
    entry_records = res_entries.scalars().all()

    data = [
        {
            "id": str(e.id),
            "entry_id": e.entry_id,
            "original_path": e.original_path,
            "normalized_path": e.normalized_path,
            "filename": e.filename,
            "extension": e.extension,
            "entry_type": e.entry_type,
            "compressed_size": e.compressed_size,
            "uncompressed_size": e.uncompressed_size,
            "compression_method": e.compression_method,
            "checksum": e.checksum,
            "encrypted": e.encrypted,
            "is_directory": e.is_directory,
            "is_symlink": e.is_symlink,
            "is_nested_archive": e.is_nested_archive,
            "detection_result": e.detection_result,
            "extracted_file_id": str(e.extracted_file_id) if e.extracted_file_id else None,
            "processing_status": e.processing_status,
            "error": e.error,
        }
        for e in entry_records
    ]
    return APIResponse.ok(data=data, message=f"Retrieved {len(data)} entries.")


@router.get(
    "/files/{file_id}/archive-analysis/entries/{entry_id}",
    response_model=APIResponse[dict[str, Any]],
    summary="Get single archive entry details",
)
async def get_archive_entry_by_id(
    file_id: uuid.UUID,
    entry_id: str,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Get metadata for a specific archive entry."""
    stmt = (
        select(ArchiveEntryRecord)
        .join(
            ArchiveAnalysisRecord,
            ArchiveEntryRecord.archive_analysis_id == ArchiveAnalysisRecord.id,
        )
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .where(ArchiveEntryRecord.entry_id == entry_id)
    )
    res = await db.execute(stmt)
    entry = res.scalars().first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry '{entry_id}' not found for file {file_id}.",
        )

    data = {
        "id": str(entry.id),
        "entry_id": entry.entry_id,
        "original_path": entry.original_path,
        "normalized_path": entry.normalized_path,
        "filename": entry.filename,
        "extension": entry.extension,
        "entry_type": entry.entry_type,
        "compressed_size": entry.compressed_size,
        "uncompressed_size": entry.uncompressed_size,
        "compression_method": entry.compression_method,
        "checksum": entry.checksum,
        "encrypted": entry.encrypted,
        "is_directory": entry.is_directory,
        "is_symlink": entry.is_symlink,
        "is_nested_archive": entry.is_nested_archive,
        "detection_result": entry.detection_result,
        "extracted_file_id": str(entry.extracted_file_id) if entry.extracted_file_id else None,
        "processing_status": entry.processing_status,
        "error": entry.error,
    }
    return APIResponse.ok(data=data, message="Entry details retrieved.")


@router.get(
    "/files/{file_id}/archive-analysis/tree",
    response_model=APIResponse[dict[str, Any]],
    summary="Get archive hierarchy directory tree",
)
async def get_archive_tree(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Return nested folder/file hierarchy tree."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Archive analysis not found."
        )

    json_path = record.artifacts.get("json")
    if json_path:
        local_p = local_storage.get_local_path(json_path)
        if local_p and local_p.exists():
            with open(local_p, encoding="utf-8") as f:
                doc_dict = json.load(f)
            return APIResponse.ok(
                data=doc_dict.get("hierarchy", {}), message="Hierarchy tree retrieved."
            )

    return APIResponse.ok(data={}, message="Hierarchy tree not available.")


@router.get(
    "/files/{file_id}/archive-analysis/nested-archives",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List nested archives discovered in this archive",
)
async def get_nested_archives(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Retrieve child archives discovered inside this archive."""
    stmt = select(ArchiveRelationshipRecord).where(
        ArchiveRelationshipRecord.parent_file_id == file_id
    )
    res = await db.execute(stmt)
    all_records = res.scalars().all()
    records = [
        r
        for r in all_records
        if (r.detection_result or {}).get("category") == "archive"
        or (
            r.original_path
            and r.original_path.lower().endswith(
                (".zip", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".tbz2", ".xz", ".txz")
            )
        )
    ]

    data = [
        {
            "id": str(r.id),
            "parent_file_id": str(r.parent_file_id),
            "child_file_id": str(r.child_file_id),
            "nesting_depth": r.nesting_depth,
            "original_path": r.original_path,
            "sha256": r.sha256,
            "status": r.processing_status,
        }
        for r in records
    ]
    return APIResponse.ok(data=data, message=f"Found {len(data)} nested archives.")


@router.post(
    "/files/{file_id}/archive-analysis/extract",
    response_model=APIResponse[dict[str, Any]],
    summary="Safely extract archive entries",
)
async def extract_archive_entries(
    file_id: uuid.UUID,
    payload: AnalyzeArchiveRequest | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Trigger safe extraction of archive contents (mode=extract_only)."""
    pw = payload.password if payload else None
    doc = await archive_pipeline.process_and_persist(
        file_id=file_id,
        session=db,
        mode="extract_only",
        password=pw,
    )
    return APIResponse.ok(data=doc.model_dump(), message="Extraction completed.")


@router.post(
    "/files/{file_id}/archive-analysis/analyze-selected",
    response_model=APIResponse[dict[str, Any]],
    summary="Extract and analyze selective archive entries",
)
async def analyze_selected_entries(
    file_id: uuid.UUID,
    payload: AnalyzeSelectedRequest,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Extract and analyze specific entries selected by user."""
    doc = await archive_pipeline.process_and_persist(
        file_id=file_id,
        session=db,
        mode="selective",
        selected_entry_ids=payload.entry_ids,
        password=payload.password,
    )
    return APIResponse.ok(
        data=doc.model_dump(), message="Selective extraction and analysis complete."
    )


@router.get(
    "/files/{file_id}/archive-analysis/extraction-status",
    response_model=APIResponse[dict[str, Any]],
    summary="Get extraction status and progress",
)
async def get_extraction_status(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Check status and counts of extraction."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Archive analysis not found."
        )

    data = {
        "archive_id": str(record.id),
        "status": record.status,
        "processing_mode": record.processing_mode,
        "entry_count": record.entry_count,
        "extracted_size": record.extracted_size,
        "safety_report": record.safety_report,
    }
    return APIResponse.ok(data=data, message="Extraction status retrieved.")


@router.get(
    "/files/{file_id}/archive-analysis/children",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="List extracted child files and provenance",
)
async def get_archive_children(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[dict[str, Any]]]:
    """Retrieve all files extracted from this archive."""
    stmt = (
        select(ArchiveRelationshipRecord)
        .where(ArchiveRelationshipRecord.parent_file_id == file_id)
        .order_by(ArchiveRelationshipRecord.nesting_depth)
    )
    res = await db.execute(stmt)
    relationships = res.scalars().all()

    data = [
        {
            "id": str(r.id),
            "parent_file_id": str(r.parent_file_id),
            "child_file_id": str(r.child_file_id),
            "nesting_depth": r.nesting_depth,
            "original_path": r.original_path,
            "extracted_storage_reference": r.extracted_storage_reference,
            "sha256": r.sha256,
            "detection_result": r.detection_result,
            "processing_status": r.processing_status,
        }
        for r in relationships
    ]
    return APIResponse.ok(data=data, message=f"Retrieved {len(data)} child files.")


@router.get(
    "/files/{file_id}/archive-analysis/security-report",
    response_model=APIResponse[dict[str, Any]],
    summary="Get security assessment and audit report",
)
async def get_archive_security_report(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve detailed security audit report."""
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Archive analysis not found."
        )

    sec_path = record.artifacts.get("security_report")
    if sec_path:
        local_p = local_storage.get_local_path(sec_path)
        if local_p and local_p.exists():
            with open(local_p, encoding="utf-8") as f:
                sec_dict = json.load(f)
            return APIResponse.ok(data=sec_dict, message="Security report retrieved.")

    return APIResponse.ok(
        data=record.safety_report, message="Security report retrieved from record."
    )


@router.get(
    "/files/{file_id}/archive-analysis/export/{format}",
    summary="Export archive intelligence reports and manifests",
)
async def export_archive_artifact(
    file_id: uuid.UUID,
    format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download export artifact (json, markdown, text, manifest, tree, extraction_report, security_report, child_manifest)."""
    fmt = format.lower().strip()
    stmt = (
        select(ArchiveAnalysisRecord)
        .where(ArchiveAnalysisRecord.file_id == file_id)
        .order_by(desc(ArchiveAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Archive analysis record not found."
        )

    key_map = {
        "json": "json",
        "markdown": "markdown",
        "md": "markdown",
        "text": "text",
        "txt": "text",
        "manifest": "manifest",
        "tree": "tree",
        "extraction_report": "extraction_report",
        "security_report": "security_report",
        "child_manifest": "child_manifest",
    }
    artifact_key = key_map.get(fmt)
    if not artifact_key or artifact_key not in record.artifacts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported or unavailable export format '{format}'.",
        )

    rel_path = record.artifacts[artifact_key]
    local_p = local_storage.get_local_path(rel_path)
    if not local_p or not local_p.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export artifact not found on storage."
        )

    media_types = {
        "json": "application/json",
        "markdown": "text/markdown",
        "text": "text/plain",
        "manifest": "application/json",
        "tree": "text/plain",
        "extraction_report": "application/json",
        "security_report": "application/json",
        "child_manifest": "application/json",
    }

    content = local_p.read_bytes()
    return Response(
        content=content,
        media_type=media_types.get(artifact_key, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="archive_{str(file_id)[:8]}_{artifact_key}.{fmt}"'
        },
    )
