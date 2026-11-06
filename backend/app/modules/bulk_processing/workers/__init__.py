"""Workers package for Phase 12."""

from app.modules.bulk_processing.workers.scalable_worker import (
    ScalableWorker,
    scalable_worker,
)

__all__ = ["ScalableWorker", "scalable_worker"]
