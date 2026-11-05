"""Storage provider plugin interface."""

from abc import abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.plugins.interfaces.base import ProcessingPluginInterface


class StorageProviderInterface(ProcessingPluginInterface):
    """Interface for saving, reading, and managing binary files across local/cloud backends."""

    @abstractmethod
    async def save_file(
        self,
        destination_key: str,
        content: bytes | BinaryIO,
        folder: str = "uploads",
    ) -> str:
        """Save file content and return the persistent relative storage identifier."""
        pass

    @abstractmethod
    async def read_file(self, storage_path: str) -> bytes:
        """Read full binary content from storage."""
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        pass

    @abstractmethod
    def get_local_path(self, storage_path: str) -> Path | None:
        """Return a local filesystem Path if available, or None for pure remote storage."""
        pass
