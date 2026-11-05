"""Plugin management and introspection endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from app.domain.schemas.api_response import APIResponse
from app.domain.schemas.plugins import PluginListResponse, PluginMetadataSchema
from app.plugins.interfaces.base import PluginType
from app.plugins.registry.registry import plugin_registry

router = APIRouter(prefix="/plugins", tags=["Plugins & Extensions"])


@router.get("", response_model=APIResponse[PluginListResponse])
async def list_plugins(
    plugin_type: PluginType | None = Query(None, description="Filter plugins by type"),
) -> APIResponse[PluginListResponse]:
    """Retrieve all discovered and registered plugins in the DocuMind ecosystem."""
    plugins_meta = plugin_registry.list_plugins(plugin_type=plugin_type)
    items = [
        PluginMetadataSchema(
            name=p.name,
            version=p.version,
            description=p.description,
            author=p.author,
            plugin_type=p.plugin_type.value,
            supported_formats=p.supported_formats,
            required_dependencies=p.required_dependencies,
            hardware_acceleration=p.hardware_acceleration,
            is_available=p.is_available,
            config_schema=p.config_schema,
        )
        for p in plugins_meta
    ]

    return APIResponse.ok(
        data=PluginListResponse(total_plugins=len(items), plugins=items),
        message="Plugins retrieved successfully.",
    )


@router.get("/{name}", response_model=APIResponse[PluginMetadataSchema])
async def get_plugin_details(name: str) -> APIResponse[PluginMetadataSchema]:
    """Retrieve detailed metadata for a registered plugin by name."""
    plugin = plugin_registry.get_plugin(name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found in registry.",
        )

    p = plugin.metadata
    schema = PluginMetadataSchema(
        name=p.name,
        version=p.version,
        description=p.description,
        author=p.author,
        plugin_type=p.plugin_type.value,
        supported_formats=p.supported_formats,
        required_dependencies=p.required_dependencies,
        hardware_acceleration=p.hardware_acceleration,
        is_available=p.is_available,
        config_schema=p.config_schema,
    )
    return APIResponse.ok(data=schema, message=f"Plugin '{name}' details.")
