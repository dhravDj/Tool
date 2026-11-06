"""Configuration and safety thresholds for Archive Intelligence Engine."""

from pydantic import BaseModel, Field


class ArchiveSafetyConfig(BaseModel):
    """Configurable safety thresholds and resource limits for archive processing."""

    max_nesting_depth: int = Field(default=5, description="Maximum nested archive recursion depth")
    max_entries_per_archive: int = Field(
        default=10000, description="Maximum entries allowed per archive"
    )
    max_total_entries_per_job: int = Field(
        default=50000, description="Maximum cumulative entries across job"
    )
    max_single_file_size_bytes: int = Field(
        default=500 * 1024 * 1024,
        description="Maximum uncompressed size for a single extracted file (500 MB)",
    )
    max_total_extracted_size_bytes: int = Field(
        default=2 * 1024 * 1024 * 1024,
        description="Maximum cumulative extracted size per job (2 GB)",
    )
    max_archive_size_bytes: int = Field(
        default=1024 * 1024 * 1024,
        description="Maximum input archive file size (1 GB)",
    )
    max_path_length: int = Field(default=1024, description="Maximum characters allowed in path")
    max_extraction_time_seconds: int = Field(
        default=300,
        description="Maximum execution timeout per extraction job in seconds",
    )
    max_compression_ratio: float = Field(
        default=100.0,
        description="Maximum allowed compression ratio before flagging as archive bomb",
    )
    max_concurrent_jobs: int = Field(default=2, description="Maximum concurrent extraction jobs")
    chunk_size_bytes: int = Field(
        default=64 * 1024, description="Chunk size for streaming decompression (64 KB)"
    )


# Global default configuration instance
archive_config = ArchiveSafetyConfig()
