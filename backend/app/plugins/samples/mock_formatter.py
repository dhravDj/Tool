"""Sample output formatter plugin."""

from typing import Any

from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.extractor import ExtractionResult
from app.plugins.interfaces.formatter import OutputFormatterInterface


class MockMarkdownFormatter(OutputFormatterInterface):
    """Sample formatter converting ExtractionResult to Markdown bytes."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="mock_markdown_formatter",
            version="1.0.0",
            description="Phase 1 sample formatter outputting Markdown.",
            plugin_type=PluginType.FORMATTER,
            supported_formats=["markdown", "md"],
            required_dependencies=[],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    @property
    def target_format(self) -> str:
        return "markdown"

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        return True

    async def format(
        self,
        result: ExtractionResult,
        options: dict[str, Any] | None = None,
    ) -> bytes:
        md = f"# Extracted Document ({result.engine_name})\n\n"
        md += f"**Pages:** {result.page_count}\n\n"
        md += "## Content\n\n"
        md += result.raw_text
        return md.encode("utf-8")
