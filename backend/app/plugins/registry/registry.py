"""Thread-safe Plugin Registry for DocuMind AI."""

import asyncio

from app.core.logging import logger
from app.plugins.interfaces.ai import AIProviderInterface
from app.plugins.interfaces.base import PluginMetadata, PluginType, ProcessingPluginInterface
from app.plugins.interfaces.detector import FileDetectorInterface
from app.plugins.interfaces.extractor import ExtractionEngineInterface
from app.plugins.interfaces.formatter import OutputFormatterInterface
from app.plugins.interfaces.storage import StorageProviderInterface


class PluginRegistry:
    """Central registry managing the discovery, lifecycle, and retrieval of DocuMind plugins."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._plugins: dict[str, ProcessingPluginInterface] = {}
        self._detectors: dict[str, FileDetectorInterface] = {}
        self._extractors: dict[str, ExtractionEngineInterface] = {}
        self._ai_providers: dict[str, AIProviderInterface] = {}
        self._storage_providers: dict[str, StorageProviderInterface] = {}
        self._formatters: dict[str, OutputFormatterInterface] = {}

    def register(self, plugin: ProcessingPluginInterface) -> None:
        """Register a plugin instance with the platform."""
        meta = plugin.metadata
        if meta.name in self._plugins:
            logger.warning(f"Plugin '{meta.name}' is already registered. Overwriting.")

        self._plugins[meta.name] = plugin

        if isinstance(plugin, FileDetectorInterface):
            self._detectors[meta.name] = plugin
        elif isinstance(plugin, ExtractionEngineInterface):
            self._extractors[meta.name] = plugin
        elif isinstance(plugin, AIProviderInterface):
            self._ai_providers[meta.name] = plugin
        elif isinstance(plugin, StorageProviderInterface):
            self._storage_providers[meta.name] = plugin
        elif isinstance(plugin, OutputFormatterInterface):
            self._formatters[meta.name] = plugin

        logger.info(
            f"Registered plugin: {meta.name} (type: {meta.plugin_type}, version: {meta.version})"
        )

    def unregister(self, plugin_name: str) -> None:
        """Remove a plugin from the registry."""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            self._detectors.pop(plugin_name, None)
            self._extractors.pop(plugin_name, None)
            self._ai_providers.pop(plugin_name, None)
            self._storage_providers.pop(plugin_name, None)
            self._formatters.pop(plugin_name, None)
            logger.info(f"Unregistered plugin: {plugin_name}")

    def get_plugin(self, name: str) -> ProcessingPluginInterface | None:
        """Retrieve any registered plugin by unique name."""
        return self._plugins.get(name)

    def get_detector(self, name: str) -> FileDetectorInterface | None:
        return self._detectors.get(name)

    def get_extractor(self, name: str) -> ExtractionEngineInterface | None:
        return self._extractors.get(name)

    def get_ai_provider(self, name: str) -> AIProviderInterface | None:
        return self._ai_providers.get(name)

    def get_storage_provider(self, name: str) -> StorageProviderInterface | None:
        return self._storage_providers.get(name)

    def get_formatter(self, name: str) -> OutputFormatterInterface | None:
        return self._formatters.get(name)

    def list_plugins(self, plugin_type: PluginType | None = None) -> list[PluginMetadata]:
        """List metadata descriptors for all registered plugins, optionally filtered by type."""
        plugins: list[ProcessingPluginInterface] = list(self._plugins.values())
        if plugin_type:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        return [p.metadata for p in plugins]

    def find_extractors_for_format(self, mime_or_ext: str) -> list[ExtractionEngineInterface]:
        """Find all registered extraction engines supporting a particular MIME type or file extension."""
        target = mime_or_ext.lower().strip(".")
        matches = []
        for extractor in self._extractors.values():
            supported = [fmt.lower().strip(".") for fmt in extractor.metadata.supported_formats]
            if target in supported or "*" in supported:
                matches.append(extractor)
        return matches

    async def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        for name, plugin in list(self._plugins.items()):
            try:
                await plugin.initialize()
                logger.info(f"Successfully initialized plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{name}': {e}", exc_info=True)

    async def shutdown_all(self) -> None:
        """Shutdown all registered plugins."""
        for name, plugin in list(self._plugins.items()):
            try:
                await plugin.shutdown()
                logger.info(f"Cleanly shut down plugin: {name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin '{name}': {e}", exc_info=True)


# Global singleton registry instance
plugin_registry = PluginRegistry()
