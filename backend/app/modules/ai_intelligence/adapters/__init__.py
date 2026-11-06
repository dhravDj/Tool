"""Universal Content Adapters for Phases 1–10 Normalization."""

from app.modules.ai_intelligence.adapters.archive_adapter import ArchiveContentAdapter
from app.modules.ai_intelligence.adapters.audio_adapter import AudioContentAdapter
from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.adapters.code_adapter import CodeContentAdapter
from app.modules.ai_intelligence.adapters.document_adapter import DocumentContentAdapter
from app.modules.ai_intelligence.adapters.image_adapter import ImageContentAdapter
from app.modules.ai_intelligence.adapters.presentation_adapter import PresentationContentAdapter
from app.modules.ai_intelligence.adapters.registry import (
    ContentAdapterRegistry,
    content_adapter_registry,
)
from app.modules.ai_intelligence.adapters.spreadsheet_adapter import SpreadsheetContentAdapter
from app.modules.ai_intelligence.adapters.structured_data_adapter import (
    StructuredDataContentAdapter,
)
from app.modules.ai_intelligence.adapters.video_adapter import VideoContentAdapter

__all__ = [
    "BaseContentAdapter",
    "compute_content_hash",
    "DocumentContentAdapter",
    "ImageContentAdapter",
    "SpreadsheetContentAdapter",
    "PresentationContentAdapter",
    "AudioContentAdapter",
    "VideoContentAdapter",
    "CodeContentAdapter",
    "StructuredDataContentAdapter",
    "ArchiveContentAdapter",
    "ContentAdapterRegistry",
    "content_adapter_registry",
]
