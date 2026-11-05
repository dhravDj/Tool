"""System information, platform statistics, and resource endpoints."""

import platform
import shutil
from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.domain.enums import FormatCategory
from app.domain.schemas.api_response import APIResponse
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
