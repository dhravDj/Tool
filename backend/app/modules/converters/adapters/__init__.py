"""Adapters package mapping engine results to UniversalContent."""

from app.modules.converters.adapters.archive_adapter import ArchiveAdapter
from app.modules.converters.adapters.audio_adapter import AudioAdapter
from app.modules.converters.adapters.code_adapter import CodeAdapter
from app.modules.converters.adapters.document_adapter import DocumentAdapter
from app.modules.converters.adapters.image_adapter import ImageAdapter
from app.modules.converters.adapters.presentation_adapter import PresentationAdapter
from app.modules.converters.adapters.spreadsheet_adapter import SpreadsheetAdapter
from app.modules.converters.adapters.structured_adapter import StructuredDataAdapter
from app.modules.converters.adapters.video_adapter import VideoAdapter

__all__ = [
    "ArchiveAdapter",
    "AudioAdapter",
    "CodeAdapter",
    "DocumentAdapter",
    "ImageAdapter",
    "PresentationAdapter",
    "SpreadsheetAdapter",
    "StructuredDataAdapter",
    "VideoAdapter",
]
