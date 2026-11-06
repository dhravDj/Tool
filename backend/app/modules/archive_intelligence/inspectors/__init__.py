"""Archive inspectors package."""

from app.modules.archive_intelligence.inspectors.base import BaseArchiveInspector
from app.modules.archive_intelligence.inspectors.gzip_inspector import GzipInspector
from app.modules.archive_intelligence.inspectors.registry import (
    ArchiveInspectorRegistry,
    inspector_registry,
)
from app.modules.archive_intelligence.inspectors.sevenzip_inspector import SevenZipInspector
from app.modules.archive_intelligence.inspectors.tar_inspector import TarInspector
from app.modules.archive_intelligence.inspectors.zip_inspector import ZipInspector

__all__ = [
    "ArchiveInspectorRegistry",
    "BaseArchiveInspector",
    "GzipInspector",
    "SevenZipInspector",
    "TarInspector",
    "ZipInspector",
    "inspector_registry",
]
