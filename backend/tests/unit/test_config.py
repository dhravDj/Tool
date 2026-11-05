"""Unit tests for configuration loading and validation."""

from pathlib import Path

from app.core.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.APP_NAME == "DocuMind AI"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.AI_MODE == "local"
    assert settings.CLOUD_PROCESSING_ENABLED is False
    assert settings.STORAGE_BACKEND == "local"
    assert settings.MAX_UPLOAD_SIZE_BYTES > 0


def test_settings_storage_paths():
    settings = Settings()
    paths = settings.storage_paths
    assert "root" in paths
    assert "uploads" in paths
    assert "temporary" in paths
    assert "processed" in paths
    assert "assets" in paths
    assert isinstance(paths["uploads"], Path)


def test_cors_origins_parsing():
    settings = Settings(BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"])
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
