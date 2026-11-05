"""File format registry discovery endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.detection import FormatDetailSchema, FormatListResponse
from app.modules.formats.categories import FormatCategory
from app.modules.formats.registry import format_registry
from app.modules.formats.support_status import SupportStatus

router = APIRouter(prefix="/formats", tags=["Format Registry"])


@router.get("", response_model=APIResponse[FormatListResponse])
async def list_formats(
    category: FormatCategory | None = Query(None, description="Filter by format category"),
    support_status: SupportStatus | None = Query(None, description="Filter by support status"),
) -> APIResponse[FormatListResponse]:
    """Retrieve catalog of all formats recognized by the Universal File Intelligence Platform."""
    formats = format_registry.list_formats(category=category, support_status=support_status)
    items = [
        FormatDetailSchema(
            format_id=f.format_id,
            canonical_name=f.canonical_name,
            display_name=f.display_name,
            category=f.category.value,
            mime_types=f.mime_types,
            extensions=f.extensions,
            is_container=f.is_container,
            container_type=f.container_type,
            support_status=f.support_status.value,
            extraction_plugin_id=f.extraction_plugin_id,
            version_info=f.version_info,
            description=f.description,
        )
        for f in formats
    ]
    return APIResponse.ok(
        data=FormatListResponse(total_formats=len(items), formats=items),
        message=f"Retrieved {len(items)} format specifications.",
    )


@router.get("/{format_id}", response_model=APIResponse[FormatDetailSchema])
async def get_format(format_id: str) -> APIResponse[FormatDetailSchema]:
    """Retrieve detailed specification for a specific file format."""
    fmt = format_registry.get_by_id(format_id)
    if not fmt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Format '{format_id}' not found in registry.",
        )

    data = FormatDetailSchema(
        format_id=fmt.format_id,
        canonical_name=fmt.canonical_name,
        display_name=fmt.display_name,
        category=fmt.category.value,
        mime_types=fmt.mime_types,
        extensions=fmt.extensions,
        is_container=fmt.is_container,
        container_type=fmt.container_type,
        support_status=fmt.support_status.value,
        extraction_plugin_id=fmt.extraction_plugin_id,
        version_info=fmt.version_info,
        description=fmt.description,
    )
    return APIResponse.ok(data=data, message=f"Format details for '{format_id}'.")
