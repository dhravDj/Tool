"""Content Deduplication and Idempotency Subsystem (Phase 12).

Enforces:
1. SHA-256 and content-hash based duplicate detection.
2. Strict per-user tenant isolation: Private data is NEVER leaked across users.
3. Analysis reuse only when owner matches and prior extraction was successful.
4. Transparent logging of deduplication decisions ('new', 'reused', 'skipped').
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import FileStatus
from app.infrastructure.database.models import FileRecord

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """Manages content deduplication and analysis reuse while enforcing user privacy boundaries."""

    async def inspect_file_deduplication(
        self,
        session: AsyncSession,
        owner_id: uuid.UUID | None,
        sha256: str,
        file_size: int,
        force_reprocess: bool = False,
    ) -> tuple[FileRecord | None, str]:
        """Checks if a matching file already exists for this owner and can be safely reused.

        Returns:
            (existing_file_record, decision_str)
            where decision_str is 'reused', 'new', or 'force_new'.
        """
        if force_reprocess or not sha256:
            return None, "new"

        # Query existing files for this specific owner with matching hash and size
        stmt = (
            select(FileRecord)
            .where(
                FileRecord.sha256 == sha256,
                FileRecord.file_size == file_size,
            )
            .options(
                selectinload(FileRecord.extractions),
                selectinload(FileRecord.knowledge_documents),
            )
        )

        if owner_id is not None:
            # Enforce strict user isolation
            stmt = stmt.where(FileRecord.owner_id == owner_id)
        else:
            # Anonymous / shared uploads
            stmt = stmt.where(FileRecord.owner_id.is_(None))

        res = await session.execute(stmt)
        candidates = res.scalars().all()

        for cand in candidates:
            # Check if this candidate completed processing successfully
            if cand.status in (FileStatus.PROCESSED.value, "processed"):
                logger.info(
                    f"Deduplication hit: Reusing existing FileRecord {cand.id} for sha256 {sha256[:12]} (owner: {owner_id})"
                )
                return cand, "reused"

        return None, "new"

    async def check_duplicate(
        self,
        session: AsyncSession,
        sha256_hash: str,
        file_size: int,
        owner_id: uuid.UUID | None = None,
        force_reprocess: bool = False,
    ) -> Any:
        cand, decision = await self.inspect_file_deduplication(
            session=session,
            owner_id=owner_id,
            sha256=sha256_hash,
            file_size=file_size,
            force_reprocess=force_reprocess,
        )
        from pydantic import BaseModel

        class DedupResult(BaseModel):
            is_duplicate: bool
            existing_file_id: uuid.UUID | None
            dedup_decision: str

        return DedupResult(
            is_duplicate=(cand is not None),
            existing_file_id=cand.id if cand else None,
            dedup_decision="duplicate" if cand is not None else decision,
        )


deduplication_engine = DeduplicationEngine()
