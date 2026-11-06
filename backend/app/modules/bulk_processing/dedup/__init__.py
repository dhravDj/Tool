"""Deduplication package for Phase 12."""

from app.modules.bulk_processing.dedup.deduplicator import (
    DeduplicationEngine,
    deduplication_engine,
)

__all__ = ["DeduplicationEngine", "deduplication_engine"]
