"""Application configuration module using Pydantic Settings."""

import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """DocuMind AI platform settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 1. Application Settings
    APP_NAME: str = "DocuMind AI"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-this-to-a-secure-random-secret-key-min-32-chars-documind-ai"

    # Server Host & Port
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173

    # CORS
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    loaded = json.loads(v)
                    if isinstance(loaded, list):
                        return [str(x) for x in loaded]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # 2. Database Settings (PostgreSQL)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "documind"
    POSTGRES_PASSWORD: str = "documind_secure_password"
    POSTGRES_DB: str = "documind_db"
    DATABASE_URL: str | None = None
    SYNC_DATABASE_URL: str | None = None
    DB_POOL_RECYCLE: int = 1800  # Recycle idle pooled connections after 30 minutes
    DB_POOL_TIMEOUT: int = 15  # Connection acquire timeout in seconds

    @property
    def async_database_uri(self) -> str:
        """Construct or return the asynchronous SQLAlchemy database URI."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_uri(self) -> str:
        """Construct or return the synchronous SQLAlchemy database URI (for Alembic)."""
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # 3. Cache & Queue Settings (Redis)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_URL: str | None = None

    @property
    def redis_uri(self) -> str:
        """Construct or return the Redis connection URI."""
        if self.REDIS_URL:
            return self.REDIS_URL
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 4. Storage Configuration
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_ROOT: str = "./storage"
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB

    @property
    def storage_paths(self) -> dict[str, Path]:
        """Resolved local storage directory paths."""
        root = Path(self.STORAGE_LOCAL_ROOT).resolve()
        return {
            "root": root,
            "uploads": root / "uploads",
            "temporary": root / "temporary",
            "processed": root / "processed",
            "assets": root / "assets",
        }

    # S3 / Object Storage (Optional for Phase 1)
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET_NAME: str = "documind-storage"
    S3_REGION: str = "us-east-1"

    # 5. Extraction & OCR Configuration (Phase 3)
    OCR_ENABLED: bool = True
    OCR_ENGINE: str = "tesseract"
    OCR_CONFIDENCE_THRESHOLD: float = 0.60
    OCR_DENSITY_THRESHOLD_CHARS: int = 40  # Trigger OCR if page text chars < 40
    MAX_EXTRACTION_PAGE_LIMIT: int = 50000  # Defensive cap: up to 50,000 pages for massive dockets/books
    EXTRACTION_TIMEOUT_SECONDS: int = 600  # 10 minutes for massive files

    # 6. AI Engine Configuration (Local-first & Sovereign)
    AI_MODE: str = "local"  # local | cloud | hybrid
    LOCAL_MODEL_PROVIDER: str = "ollama"
    LOCAL_INFERENCE_DEVICE: str = "cpu"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Hardware Governor & Concurrency (Ryzen 7 5800H + RTX 3050 4GB VRAM)
    MAX_PARALLEL_WORKERS: int = 4
    GPU_MAX_CONCURRENT_INFERENCE: int = 1
    VISION_ENGINE_DEFAULT: str = "documind-heuristic-cv-v1"
    VISION_DEVICE: str = "cpu"

    CLOUD_PROCESSING_ENABLED: bool = False
    CLOUD_MODEL_PROVIDER: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None


settings = Settings()
