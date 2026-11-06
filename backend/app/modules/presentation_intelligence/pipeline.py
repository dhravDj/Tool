"""Presentation Intelligence Pipeline Orchestrator."""

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import FileRecord, PresentationAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.presentation_intelligence.adapters.base import BasePresentationAdapter
from app.modules.presentation_intelligence.adapters.odp_adapter import (
    ODPPresentationAdapter,
)
from app.modules.presentation_intelligence.adapters.ppt_adapter import (
    PPTPresentationAdapter,
)
from app.modules.presentation_intelligence.adapters.pptx_adapter import (
    PPTXPresentationAdapter,
)
from app.modules.presentation_intelligence.generators.json_generator import (
    PresentationJSONGenerator,
)
from app.modules.presentation_intelligence.generators.manifest_generator import (
    PresentationManifestGenerator,
)
from app.modules.presentation_intelligence.generators.markdown_generator import (
    PresentationMarkdownGenerator,
)
from app.modules.presentation_intelligence.generators.text_generator import (
    PresentationTextGenerator,
)
from app.modules.presentation_intelligence.schemas.presentation_document import (
    PresentationDocument,
    PresentationManifest,
)

logger = logging.getLogger(__name__)


class UnsupportedPresentationFormatError(Exception):
    """Raised when an unhandled format is passed to presentation intelligence."""
    pass


class PresentationIntelligencePipeline:
    """Orchestrates format routing, extraction, artifact generation, and persistence for presentations."""

    def __init__(self) -> None:
        self.adapters: dict[str, BasePresentationAdapter] = {
            "pptx": PPTXPresentationAdapter(),
            "ppt": PPTPresentationAdapter(),
            "odp": ODPPresentationAdapter(),
        }

    def list_supported_formats(self) -> list[str]:
        return sorted(self.adapters.keys())

    def get_adapter(self, format_id: str) -> BasePresentationAdapter:
        fmt = format_id.lower().strip()
        adapter = self.adapters.get(fmt)
        if not adapter:
            raise UnsupportedPresentationFormatError(
                f"Unsupported presentation format '{format_id}'. Supported formats: {self.list_supported_formats()}"
            )
        return adapter

    async def extract_document(
        self,
        file_path: Path,
        format_id: str,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> tuple[PresentationDocument, list[dict[str, Any]]]:
        """Extract canonical presentation document and assets using matching format adapter."""
        adapter = self.get_adapter(format_id)
        opts = options or {}
        doc_id = opts.get("document_id", f"pres_doc_{uuid.uuid4().hex[:12]}")
        file_id = opts.get("file_id", str(uuid.uuid4()))

        return await adapter.extract_presentation(
            file_path=file_path,
            document_id=doc_id,
            file_id=file_id,
            original_filename=original_filename,
            max_slides=opts.get("max_slides", 500),
            options=opts,
        )

    async def analyze_file_record(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> tuple[PresentationDocument, PresentationManifest]:
        """Execute end-to-end presentation intelligence for an ingested FileRecord."""
        start_time = time.monotonic()
        opts = dict(options or {})

        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise ValueError(f"FileRecord with ID {file_id} not found.")

        # Determine format
        fmt = (
            record.detection_format_id
            or record.actual_extension
            or record.extension
            or "pptx"
        ).lower()

        # Resolve path
        file_path = local_storage._resolve_safe_path(record.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Storage path {record.storage_path} does not exist.")

        # Execute extraction
        doc, raw_assets = await self.extract_document(
            file_path=file_path,
            format_id=fmt,
            original_filename=record.original_filename,
            options={"file_id": str(file_id), **opts},
        )

        # Generate and save artifacts
        artifacts: dict[str, str] = {}
        storage_folder = f"processed/{file_id}/presentation"

        # 1. Save embedded assets to storage
        for raw_asset in raw_assets:
            try:
                asset_id = raw_asset["asset_id"]
                blob = raw_asset["blob"]
                asset_fmt = raw_asset["format"]
                dest_key = f"assets/{asset_id}.{asset_fmt}"
                asset_storage_path = await local_storage.save_file(
                    destination_key=dest_key,
                    content=blob,
                    folder=storage_folder,
                )
                # Link path in document asset
                for doc_asset in doc.assets:
                    if doc_asset.asset_id == asset_id:
                        doc_asset.storage_path = asset_storage_path
                        break
            except Exception as e:
                logger.warning(f"Could not persist asset {raw_asset.get('asset_id')}: {e}")

        # 2. JSON canonical document
        json_str = PresentationJSONGenerator.generate(doc)
        json_path = await local_storage.save_file(
            destination_key="presentation_document.json",
            content=json_str.encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["json"] = json_path

        # 3. Markdown presentation report
        md_str = PresentationMarkdownGenerator.generate(doc)
        md_path = await local_storage.save_file(
            destination_key="presentation_report.md",
            content=md_str.encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["markdown"] = md_path

        # 4. Plain text presentation stream
        txt_str = PresentationTextGenerator.generate(doc)
        txt_path = await local_storage.save_file(
            destination_key="presentation_text.txt",
            content=txt_str.encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["text"] = txt_path

        # 5. Manifest
        duration = time.monotonic() - start_time
        manifest = PresentationManifestGenerator.generate(
            doc=doc,
            source_filename=record.original_filename,
            source_format=fmt,
            processing_time_seconds=duration,
            artifacts=artifacts,
        )
        manifest_path = await local_storage.save_file(
            destination_key="presentation_manifest.json",
            content=manifest.model_dump_json(indent=2).encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["manifest"] = manifest_path

        # 6. Persist to PostgreSQL database
        total_elements = sum(len(s.elements) for s in doc.slides)
        has_notes = len(doc.speaker_notes) > 0
        has_tables = len(doc.tables) > 0
        has_charts = len(doc.charts) > 0
        has_diagrams = len(doc.diagrams) > 0
        has_images = len(doc.assets) > 0

        analysis_record = PresentationAnalysisRecord(
            file_id=file_id,
            status="completed",
            format=fmt,
            slide_count=doc.slide_count,
            hidden_slide_count=doc.metadata.hidden_slide_count,
            total_elements=total_elements,
            has_notes=has_notes,
            has_tables=has_tables,
            has_charts=has_charts,
            has_diagrams=has_diagrams,
            has_images=has_images,
            artifacts=artifacts,
            presentation_metadata=doc.metadata.model_dump(),
            warnings=doc.warnings,
            engine_version=doc.extraction_metadata.get("engine_version", "6.0.0"),
            confidence=doc.confidence,
            processing_duration=duration,
        )
        session.add(analysis_record)
        await session.commit()
        await session.refresh(analysis_record)

        return doc, manifest


# Global pipeline singleton
presentation_pipeline = PresentationIntelligencePipeline()
