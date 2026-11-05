"""Plugin schemas for reporting registered plugins and capabilities."""

from typing import Any

from pydantic import BaseModel, Field


class PluginMetadataSchema(BaseModel):
    name: str
    version: str
    description: str
    author: str | None = "DocuMind Core"
    plugin_type: str = Field(description="detector | extractor | ai_provider | storage | formatter")
    supported_formats: list[str] = Field(default_factory=list)
    required_dependencies: list[str] = Field(default_factory=list)
    hardware_acceleration: str = Field(default="cpu", description="cpu | cuda | rocm | any")
    is_available: bool = True
    config_schema: dict[str, Any] | None = None


class PluginListResponse(BaseModel):
    total_plugins: int
    plugins: list[PluginMetadataSchema]
