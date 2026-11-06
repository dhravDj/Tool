"""Registry managing structured data intelligence engines."""

from typing import Any

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.engines.json_engine import JSONEngine
from app.modules.structured_data_intelligence.engines.parquet_engine import ParquetEngine
from app.modules.structured_data_intelligence.engines.toml_engine import TOMLEngine
from app.modules.structured_data_intelligence.engines.xml_engine import XMLEngine
from app.modules.structured_data_intelligence.engines.yaml_engine import YAMLEngine


class StructuredEngineRegistry:
    """Registry coordinating structured data engines for JSON, XML, YAML, TOML, and Parquet."""

    def __init__(self) -> None:
        self.engines: list[BaseStructuredEngine] = [
            JSONEngine(),
            XMLEngine(),
            YAMLEngine(),
            TOMLEngine(),
            ParquetEngine(),
        ]
        self._by_format: dict[str, BaseStructuredEngine] = {}
        for eng in self.engines:
            self._by_format[eng.format] = eng
            for ext in eng.supported_extensions:
                self._by_format[ext] = eng

    def get_engine_for_format(self, format_id: str) -> BaseStructuredEngine | None:
        """Find engine matching format name or extension."""
        return self._by_format.get(format_id.lower().strip())

    def get_engine_for_filename(self, filename: str) -> BaseStructuredEngine | None:
        """Find engine matching file extension."""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        return self._by_format.get(ext)

    def list_supported_formats(self) -> list[dict[str, Any]]:
        """List all structured data engine capabilities."""
        return [
            {
                "format": e.format,
                "supported_extensions": e.supported_extensions,
                "class": e.__class__.__name__,
            }
            for e in self.engines
        ]


structured_engine_registry = StructuredEngineRegistry()
