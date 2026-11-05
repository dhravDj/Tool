"""Local filesystem storage provider implementation."""

import shutil
from pathlib import Path
from typing import Any, BinaryIO

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import logger
from app.plugins.interfaces.base import PluginMetadata, PluginType
from app.plugins.interfaces.storage import StorageProviderInterface


class LocalStorageProvider(StorageProviderInterface):
    """Stores files on the local filesystem partitioned by category and date."""

    def __init__(self, root_dir: Path | None = None):
        self.root = root_dir or Path(settings.STORAGE_LOCAL_ROOT).resolve()

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="local_storage_provider",
            version="1.0.0",
            description="Default local filesystem storage provider.",
            plugin_type=PluginType.STORAGE,
            supported_formats=["*"],
            required_dependencies=[],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Ensure storage directory trees exist with correct permissions."""
        for folder in ["uploads", "temporary", "processed", "assets"]:
            path = self.root / folder
            path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorageProvider initialized at {self.root}")

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        """Verify storage directory exists and is writable."""
        try:
            test_file = self.root / "temporary" / ".health_check_probe"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False

    async def save_file(
        self,
        destination_key: str,
        content: bytes | BinaryIO,
        folder: str = "uploads",
    ) -> str:
        """Save file bytes or stream into storage and return the relative storage path."""
        target_dir = self.root / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / destination_key

        try:
            if isinstance(content, bytes):
                target_path.write_bytes(content)
            else:
                with open(target_path, "wb") as f:
                    shutil.copyfileobj(content, f)
            return f"{folder}/{destination_key}"
        except Exception as e:
            logger.error(f"Failed to save file {destination_key}: {e}", exc_info=True)
            raise StorageError(f"Could not write file to storage: {e}") from e

    async def read_file(self, storage_path: str) -> bytes:
        """Read full file content from relative storage path."""
        target_path = self.root / storage_path
        if not target_path.exists():
            raise StorageError(f"File not found in storage: {storage_path}")
        return target_path.read_bytes()

    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage."""
        target_path = self.root / storage_path
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        target_path = self.root / storage_path
        return target_path.exists()

    def get_local_path(self, storage_path: str) -> Path | None:
        """Return absolute Path object on the local filesystem."""
        return self.root / storage_path


# Global instance
local_storage = LocalStorageProvider()
