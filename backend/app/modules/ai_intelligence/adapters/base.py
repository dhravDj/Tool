"""Base abstract class for Universal Content Adapters."""

import hashlib
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.schemas.knowledge import KnowledgeDocument


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA256 hex digest for text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class BaseContentAdapter(ABC):
    """Abstract interface transforming extraction output into a normalized KnowledgeDocument."""

    @abstractmethod
    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        """Transform raw extracted data into unified KnowledgeDocument representation."""
        pass
