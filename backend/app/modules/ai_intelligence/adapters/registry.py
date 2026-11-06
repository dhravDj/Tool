"""Content Adapter Registry for Universal File Normalization."""

from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.archive_adapter import ArchiveContentAdapter
from app.modules.ai_intelligence.adapters.audio_adapter import AudioContentAdapter
from app.modules.ai_intelligence.adapters.base import BaseContentAdapter
from app.modules.ai_intelligence.adapters.code_adapter import CodeContentAdapter
from app.modules.ai_intelligence.adapters.document_adapter import DocumentContentAdapter
from app.modules.ai_intelligence.adapters.image_adapter import ImageContentAdapter
from app.modules.ai_intelligence.adapters.presentation_adapter import PresentationContentAdapter
from app.modules.ai_intelligence.adapters.spreadsheet_adapter import SpreadsheetContentAdapter
from app.modules.ai_intelligence.adapters.structured_data_adapter import (
    StructuredDataContentAdapter,
)
from app.modules.ai_intelligence.adapters.video_adapter import VideoContentAdapter
from app.modules.ai_intelligence.schemas.knowledge import KnowledgeDocument


class ContentAdapterRegistry:
    """Registry routing extracted/analyzed payloads to the correct ContentAdapter."""

    def __init__(self) -> None:
        self._doc_adapter = DocumentContentAdapter()
        self._img_adapter = ImageContentAdapter()
        self._sheet_adapter = SpreadsheetContentAdapter()
        self._pres_adapter = PresentationContentAdapter()
        self._audio_adapter = AudioContentAdapter()
        self._video_adapter = VideoContentAdapter()
        self._code_adapter = CodeContentAdapter()
        self._struct_adapter = StructuredDataContentAdapter()
        self._archive_adapter = ArchiveContentAdapter()

        self._type_map: dict[str, BaseContentAdapter] = {
            # Documents (Phase 3)
            "document": self._doc_adapter,
            "pdf": self._doc_adapter,
            "docx": self._doc_adapter,
            "doc": self._doc_adapter,
            "txt": self._doc_adapter,
            "text": self._doc_adapter,
            "md": self._doc_adapter,
            "markdown": self._doc_adapter,
            "rtf": self._doc_adapter,
            "odt": self._doc_adapter,
            "epub": self._doc_adapter,
            # Images (Phase 4)
            "image": self._img_adapter,
            "png": self._img_adapter,
            "jpg": self._img_adapter,
            "jpeg": self._img_adapter,
            "webp": self._img_adapter,
            "tiff": self._img_adapter,
            "bmp": self._img_adapter,
            "gif": self._img_adapter,
            # Spreadsheets (Phase 5)
            "spreadsheet": self._sheet_adapter,
            "xlsx": self._sheet_adapter,
            "xls": self._sheet_adapter,
            "csv": self._sheet_adapter,
            "tsv": self._sheet_adapter,
            "ods": self._sheet_adapter,
            # Presentations (Phase 6)
            "presentation": self._pres_adapter,
            "pptx": self._pres_adapter,
            "ppt": self._pres_adapter,
            "odp": self._pres_adapter,
            # Audio (Phase 7)
            "audio": self._audio_adapter,
            "mp3": self._audio_adapter,
            "wav": self._audio_adapter,
            "m4a": self._audio_adapter,
            "flac": self._audio_adapter,
            "ogg": self._audio_adapter,
            "aac": self._audio_adapter,
            # Video (Phase 8)
            "video": self._video_adapter,
            "mp4": self._video_adapter,
            "avi": self._video_adapter,
            "mkv": self._video_adapter,
            "mov": self._video_adapter,
            "webm": self._video_adapter,
            "flv": self._video_adapter,
            "wmv": self._video_adapter,
            # Code (Phase 9)
            "code": self._code_adapter,
            "py": self._code_adapter,
            "python": self._code_adapter,
            "js": self._code_adapter,
            "javascript": self._code_adapter,
            "ts": self._code_adapter,
            "typescript": self._code_adapter,
            "java": self._code_adapter,
            "c": self._code_adapter,
            "cpp": self._code_adapter,
            "h": self._code_adapter,
            "go": self._code_adapter,
            "rust": self._code_adapter,
            "rs": self._code_adapter,
            "sql": self._code_adapter,
            "html": self._code_adapter,
            "css": self._code_adapter,
            "sh": self._code_adapter,
            "bash": self._code_adapter,
            # Structured data (Phase 9)
            "structured_data": self._struct_adapter,
            "json": self._struct_adapter,
            "xml": self._struct_adapter,
            "yaml": self._struct_adapter,
            "yml": self._struct_adapter,
            "toml": self._struct_adapter,
            "parquet": self._struct_adapter,
            "avro": self._struct_adapter,
            # Archive (Phase 10)
            "archive": self._archive_adapter,
            "zip": self._archive_adapter,
            "tar": self._archive_adapter,
            "gz": self._archive_adapter,
            "tgz": self._archive_adapter,
            "7z": self._archive_adapter,
            "rar": self._archive_adapter,
            "bz2": self._archive_adapter,
            "xz": self._archive_adapter,
        }

    def get_adapter(self, file_type_or_format: str) -> BaseContentAdapter:
        key = (file_type_or_format or "").strip().lower()
        if key.startswith("."):
            key = key[1:]
        return self._type_map.get(key, self._doc_adapter)

    def normalize(
        self,
        file_id: str,
        filename: str,
        file_type_or_format: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        adapter = self.get_adapter(file_type_or_format)
        return adapter.normalize(
            file_id=file_id,
            filename=filename,
            data=data,
            parent_archive_id=parent_archive_id,
        )


content_adapter_registry = ContentAdapterRegistry()
