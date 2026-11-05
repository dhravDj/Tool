"""File format definitions and metadata schema."""

from dataclasses import dataclass, field

from app.modules.formats.categories import FormatCategory
from app.modules.formats.signatures import MagicSignature
from app.modules.formats.support_status import SupportStatus


@dataclass
class FileFormatDefinition:
    """Canonical specification for a recognized file format."""

    format_id: str
    canonical_name: str
    display_name: str
    category: FormatCategory
    mime_types: list[str]
    extensions: list[str]
    magic_signatures: list[MagicSignature] = field(default_factory=list)
    is_container: bool = False
    container_type: str | None = None
    support_status: SupportStatus = SupportStatus.DETECTED_AND_SUPPORTED
    extraction_plugin_id: str | None = None
    version_info: str | None = None
    description: str = ""

    @property
    def primary_extension(self) -> str:
        return self.extensions[0] if self.extensions else "bin"

    @property
    def primary_mime(self) -> str:
        return self.mime_types[0] if self.mime_types else "application/octet-stream"
