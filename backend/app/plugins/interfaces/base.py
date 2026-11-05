"""Base interfaces and metadata definitions for the DocuMind AI plugin ecosystem."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginType(str, Enum):
    DETECTOR = "detector"
    EXTRACTOR = "extractor"
    AI_PROVIDER = "ai_provider"
    STORAGE = "storage"
    FORMATTER = "formatter"


@dataclass(frozen=True)
class PluginMetadata:
    """Immutable metadata descriptor for registered plugins."""

    name: str
    version: str
    description: str
    plugin_type: PluginType
    supported_formats: list[str] = field(default_factory=list)
    required_dependencies: list[str] = field(default_factory=list)
    hardware_acceleration: str = "cpu"  # cpu | cuda | rocm | any
    author: str = "DocuMind Team"
    is_available: bool = True
    config_schema: dict[str, Any] | None = None


class ProcessingPluginInterface(ABC):
    """Universal lifecycle and contract interface for all DocuMind plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return the plugin's metadata descriptor."""
        pass

    @abstractmethod
    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize resources, check dependencies, or warm up local models."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Release held handles, clear threadpools, or close sockets."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Verify whether this plugin is healthy and ready to process requests."""
        pass
