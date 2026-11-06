"""System information, platform statistics, and resource endpoints."""

import platform
import shutil
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.core.config import settings
from app.domain.enums import FormatCategory
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import (
    FileRecord,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    ProcessingBatchRecord,
)
from app.modules.bulk_processing.capacity.system_monitor import system_monitor
from app.modules.bulk_processing.pipeline import bulk_processing_pipeline
from app.modules.bulk_processing.schemas.job import (
    ResourceUsageResponse,
    SystemCapacityResponse,
    WorkerStatusResponse,
)
from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.files.detection.mime_detector import HAS_MAGIC
from app.modules.formats.registry import format_registry
from app.plugins.registry.registry import plugin_registry

router = APIRouter(prefix="/system", tags=["System Information"])


@router.get("/status", response_model=APIResponse[dict[str, Any]])
async def get_system_status() -> APIResponse[dict[str, Any]]:
    """Retrieve platform operational status, environment settings, and disk capacity."""
    # Disk space calculation
    storage_root = settings.storage_paths["root"]
    disk_usage = {"total_gb": 0.0, "free_gb": 0.0, "used_gb": 0.0, "percent_used": 0.0}
    try:
        total, used, free = shutil.disk_usage(storage_root)
        disk_usage = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 1),
        }
    except Exception:
        pass

    all_plugins = plugin_registry.list_plugins()

    system_info = {
        "platform": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
        },
        "ai_engine": {
            "mode": settings.AI_MODE,
            "local_provider": settings.LOCAL_MODEL_PROVIDER,
            "device": settings.LOCAL_INFERENCE_DEVICE,
            "cloud_processing_enabled": settings.CLOUD_PROCESSING_ENABLED,
            "cloud_provider": settings.CLOUD_MODEL_PROVIDER,
        },
        "storage": {
            "backend": settings.STORAGE_BACKEND,
            "root_path": str(storage_root),
            "max_upload_size_mb": round(settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024), 2),
            "disk_usage": disk_usage,
        },
        "plugins_summary": {
            "total_count": len(all_plugins),
            "active_plugins": [p.name for p in all_plugins if p.is_available],
        },
        "supported_format_categories": [
            c.value for c in FormatCategory if c != FormatCategory.UNKNOWN
        ],
    }

    return APIResponse.ok(data=system_info, message="System status retrieved.")


@router.get("/detection-capabilities", response_model=APIResponse[dict[str, Any]])
async def get_detection_capabilities() -> APIResponse[dict[str, Any]]:
    """Retrieve Phase 2 Universal File Detection engine capabilities, registered formats, and pipeline layers."""
    all_formats = format_registry.list_all()
    categories_summary: dict[str, int] = {}
    for cat in format_registry.list_categories():
        categories_summary[cat.value] = len(format_registry.get_by_category(cat))

    capabilities = {
        "engine_version": UniversalFileDetector.ENGINE_VERSION,
        "libmagic_active": HAS_MAGIC,
        "total_registered_formats": len(all_formats),
        "categories_count": len(categories_summary),
        "formats_per_category": categories_summary,
        "detection_pipeline_layers": [
            {
                "step": 1,
                "name": "Validation",
                "description": "Filesystem existence, permissions, symlink checks, non-empty, and strict size limit bounds (2GB default).",
            },
            {
                "step": 2,
                "name": "Extension Analysis",
                "description": "Normalized case-insensitive compound extension mapping (.tar.gz, .docx, etc.).",
            },
            {
                "step": 3,
                "name": "Magic Byte Detection",
                "description": "Extensible binary header & offset matching for PDF, PNG, JPEG, GIF, WEBP, ZIP, 7Z, GZ, RAR, MP3, WAV, FLAC, MP4, EBML, OLE2, ELF, PE, and Fonts.",
            },
            {
                "step": 4,
                "name": "MIME Inspection",
                "description": "python-magic libmagic binary content introspection with pure-Python fallback.",
            },
            {
                "step": 5,
                "name": "Container Package Inspection",
                "description": "Defensive ZIP/OOXML (DOCX, XLSX, PPTX), ODF (ODT, ODS, ODP), and EPUB internal manifest inspection with zip bomb mitigation.",
            },
            {
                "step": 6,
                "name": "Safe Text Heuristics",
                "description": "UTF BOM identification, strict JSON / XML / SVG / HTML / TOML / CSV structural inspection, and language syntax markers.",
            },
            {
                "step": 7,
                "name": "Multi-Signal Confidence Arbitration",
                "description": "Evidence aggregation, extension mismatch flagging, corruption detection, and polyglot risk assessment.",
            },
        ],
        "limits": {
            "max_file_size_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
            "max_archive_entries_scanned": 120,
            "max_archive_decompressed_bytes": 5 * 1024 * 1024,
            "max_magic_read_bytes": 65536,
        },
    }

    return APIResponse.ok(
        data=capabilities, message="Detection capabilities retrieved successfully."
    )


@router.get("/processing-capacity", response_model=APIResponse[SystemCapacityResponse])
async def get_processing_capacity(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[SystemCapacityResponse]:
    """Retrieve live processing capacity, throughput limits, and backpressure signals."""
    capacity = await system_monitor.get_system_capacity(session)
    return APIResponse.ok(data=capacity, message="Processing capacity retrieved.")


@router.get("/worker-status", response_model=APIResponse[list[WorkerStatusResponse]])
async def get_worker_status(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[list[WorkerStatusResponse]]:
    """Retrieve active worker heartbeats and workload statuses."""
    workers = await system_monitor.get_worker_statuses(session)
    return APIResponse.ok(data=workers, message="Worker statuses retrieved.")


@router.get("/resource-usage", response_model=APIResponse[ResourceUsageResponse])
async def get_resource_usage() -> APIResponse[ResourceUsageResponse]:
    """Retrieve current host CPU, RAM, disk, and GPU hardware metrics."""
    usage = await system_monitor.get_resource_usage()
    return APIResponse.ok(data=usage, message="Resource usage retrieved.")


@router.get("/dashboard-analytics", response_model=APIResponse[dict[str, Any]])
async def get_dashboard_analytics(
    session: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve comprehensive platform metrics, distributions, recent items, and storage statistics."""
    # 1. File counts and storage bytes
    total_files_stmt = select(func.count(FileRecord.id))
    total_files = (await session.execute(total_files_stmt)).scalar() or 0

    processed_stmt = select(func.count(FileRecord.id)).where(
        FileRecord.status.in_(["ready", "completed", "processed"])
    )
    processed_files = (await session.execute(processed_stmt)).scalar() or 0

    processing_stmt = select(func.count(FileRecord.id)).where(
        FileRecord.status.in_(["processing", "detecting"])
    )
    processing_files = (await session.execute(processing_stmt)).scalar() or 0

    failed_stmt = select(func.count(FileRecord.id)).where(
        FileRecord.status.in_(["failed", "error"])
    )
    failed_files = (await session.execute(failed_stmt)).scalar() or 0

    pending_stmt = select(func.count(FileRecord.id)).where(FileRecord.status == "pending")
    pending_files = (await session.execute(pending_stmt)).scalar() or 0

    storage_bytes_stmt = select(func.sum(FileRecord.file_size))
    total_storage_bytes = (await session.execute(storage_bytes_stmt)).scalar() or 0

    # 2. File Format distribution
    cat_stmt = select(FileRecord.format_category, func.count(FileRecord.id)).group_by(
        FileRecord.format_category
    )
    cat_res = await session.execute(cat_stmt)
    format_distribution = {cat or "unknown": count for cat, count in cat_res.all()}

    # 3. Processing status distribution
    status_stmt = select(FileRecord.status, func.count(FileRecord.id)).group_by(FileRecord.status)
    status_res = await session.execute(status_stmt)
    status_distribution = {st or "unknown": count for st, count in status_res.all()}

    # 4. AI Indexing status
    ai_docs_stmt = select(func.count(KnowledgeDocumentRecord.id))
    indexed_documents = (await session.execute(ai_docs_stmt)).scalar() or 0

    ai_chunks_stmt = select(func.count(KnowledgeChunkRecord.id))
    indexed_chunks = (await session.execute(ai_chunks_stmt)).scalar() or 0

    # 5. Batches summary
    batches_stmt = select(func.count(ProcessingBatchRecord.id))
    total_batches = (await session.execute(batches_stmt)).scalar() or 0

    active_batches_stmt = select(func.count(ProcessingBatchRecord.id)).where(
        ProcessingBatchRecord.status.in_(["processing", "queued"])
    )
    active_batches = (await session.execute(active_batches_stmt)).scalar() or 0

    completed_batches_stmt = select(func.count(ProcessingBatchRecord.id)).where(
        ProcessingBatchRecord.status == "completed"
    )
    completed_batches = (await session.execute(completed_batches_stmt)).scalar() or 0

    # 6. Recent files (latest 6)
    recent_files_stmt = select(FileRecord).order_by(FileRecord.created_at.desc()).limit(6)
    recent_files_res = await session.execute(recent_files_stmt)
    recent_files = [
        {
            "id": str(f.id),
            "filename": f.original_filename,
            "format_category": f.format_category,
            "detected_mime_type": f.detected_mime_type,
            "file_size_bytes": f.file_size,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in recent_files_res.scalars().all()
    ]

    # 7. Recent batches (latest 5)
    recent_batches_stmt = (
        select(ProcessingBatchRecord).order_by(ProcessingBatchRecord.created_at.desc()).limit(5)
    )
    recent_batches_res = await session.execute(recent_batches_stmt)
    recent_batches = [
        {
            "id": str(b.id),
            "name": b.name,
            "status": b.status,
            "total_files": b.total_files,
            "completed_files": b.completed_files,
            "failed_files": b.failed_files,
            "progress_percent": b.progress_percent,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in recent_batches_res.scalars().all()
    ]

    # 8. Host capacity and queue telemetry
    capacity = await system_monitor.get_system_capacity(session)
    queue_status = await bulk_processing_pipeline.get_queue_status()

    # 9. Storage disk stats
    storage_root = settings.storage_paths["root"]
    disk_usage = {"total_gb": 0.0, "free_gb": 0.0, "used_gb": 0.0, "percent_used": 0.0}
    try:
        total, used, free = shutil.disk_usage(storage_root)
        disk_usage = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 1),
        }
    except Exception:
        pass

    data = {
        "files_summary": {
            "total_files": total_files,
            "supported_files": total_files,
            "processed_files": processed_files,
            "processing_files": processing_files,
            "failed_files": failed_files,
            "pending_files": pending_files,
            "total_storage_bytes": total_storage_bytes,
        },
        "ai_summary": {
            "indexed_documents": indexed_documents,
            "indexed_chunks": indexed_chunks,
            "unindexed_files": max(0, total_files - indexed_documents),
        },
        "batches_summary": {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "completed_batches": completed_batches,
        },
        "format_distribution": format_distribution,
        "status_distribution": status_distribution,
        "recent_files": recent_files,
        "recent_batches": recent_batches,
        "capacity": {
            "max_parallel_cpu_workers": capacity.max_parallel_cpu_workers,
            "max_concurrent_gpu_slots": capacity.max_concurrent_gpu_slots,
            "active_cpu_workers": capacity.active_cpu_slots_in_use,
            "active_gpu_workers": capacity.active_gpu_slots_in_use,
            "backpressure_active": capacity.is_under_backpressure,
            "queue_depth_total": queue_status.total_queued,
        },
        "queue_status": {
            "interactive_depth": queue_status.queues.get("interactive", 0),
            "normal_depth": queue_status.queues.get("normal", 0),
            "bulk_depth": queue_status.queues.get("bulk", 0),
            "maintenance_depth": queue_status.queues.get("maintenance", 0),
            "dead_letter_depth": queue_status.total_dead_letter,
            "in_flight": queue_status.total_processing,
            "total_queued": queue_status.total_queued,
            "active_workers_count": queue_status.active_workers_count,
        },
        "disk_storage": disk_usage,
    }
    return APIResponse.ok(data=data, message="Dashboard analytics retrieved.")
