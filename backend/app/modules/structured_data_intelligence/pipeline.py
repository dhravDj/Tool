"""Structured Data Intelligence Pipeline orchestrating JSON, XML, YAML, TOML, and Parquet engines."""

import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import FileRecord, StructuredDataAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.structured_data_intelligence.engines.registry import structured_engine_registry
from app.modules.structured_data_intelligence.generators.csv_generator import StructuredCSVGenerator
from app.modules.structured_data_intelligence.generators.json_generator import (
    StructuredJSONGenerator,
)
from app.modules.structured_data_intelligence.generators.markdown_generator import (
    StructuredMarkdownGenerator,
)
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)

logger = logging.getLogger(__name__)

SUPPORTED_STRUCTURED_FORMATS = ["json", "xml", "yaml", "toml", "parquet"]


class StructuredDataError(Exception):
    """Base exception for structured data errors."""


class UnsupportedStructuredFormatError(StructuredDataError):
    """Raised when an unhandled structured data format is encountered."""


class StructuredDataIntelligencePipeline:
    """Orchestrates structured data parsing, schema extraction, profiling, and export generation."""

    def __init__(self) -> None:
        self.engine_registry = structured_engine_registry
        self.json_generator = StructuredJSONGenerator()
        self.markdown_generator = StructuredMarkdownGenerator()
        self.csv_generator = StructuredCSVGenerator()

    def get_capabilities(self) -> dict[str, Any]:
        """Expose current system structured data capabilities."""
        return {
            "supported_formats": SUPPORTED_STRUCTURED_FORMATS,
            "installed_engines": [e["class"] for e in self.engine_registry.list_supported_formats()],
            "features": [
                "json_duplicate_key_detection",
                "json_schema_inference",
                "xml_xxe_protection",
                "yaml_safe_parsing_alias_defense",
                "toml_table_hierarchy",
                "parquet_columnar_profiling_zero_dataframe",
                "column_statistics",
                "candidate_key_inference",
            ],
            "max_file_size_bytes": getattr(settings, "MAX_STRUCTURED_FILE_SIZE", 100 * 1024 * 1024),
        }

    async def analyze_structured_data(
        self,
        file_path: Path | str,
        file_id: str,
        original_filename: str = "",
        format_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> StructuredDataDocument:
        """Perform end-to-end structured data intelligence analysis on the given local file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Structured file not found at: {path}")

        filename = original_filename or path.name

        engine = None
        if format_id:
            engine = self.engine_registry.get_engine_for_format(format_id)
        if not engine:
            engine = self.engine_registry.get_engine_for_filename(filename)

        if not engine:
            raise UnsupportedStructuredFormatError(
                f"Unsupported structured data format for file: '{filename}'"
            )

        doc = engine.analyze(
            file_path_or_bytes=path,
            file_id=file_id,
            filename=filename,
            options=options,
        )

        # Persist generated artifacts asynchronously
        try:
            json_str = self.json_generator.generate(doc)
            md_str = self.markdown_generator.generate(doc)
            csv_str = self.csv_generator.generate(doc)

            await local_storage.save_file(
                f"structured/{file_id}/structured_document.json",
                json_str.encode("utf-8"),
            )
            await local_storage.save_file(
                f"structured/{file_id}/structured_analysis.md",
                md_str.encode("utf-8"),
            )
            if csv_str:
                await local_storage.save_file(
                    f"structured/{file_id}/sample_records.csv",
                    csv_str.encode("utf-8"),
                )
        except Exception as save_err:
            logger.warning("Failed to persist structured artifacts for %s: %s", file_id, save_err)

        return doc

    async def process_and_persist(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> StructuredDataDocument:
        """Analyze structured data for a registered FileRecord, persist artifacts and StructuredDataAnalysisRecord."""
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        file_record = res.scalar_one_or_none()
        if not file_record:
            raise FileNotFoundError(f"FileRecord with ID {file_id} not found.")

        resolved = local_storage.get_local_path(file_record.storage_path)
        source_path = resolved if resolved is not None else Path(file_record.storage_path)
        fmt = (file_record.detection_format_id or file_record.actual_extension or "").lower()

        doc = await self.analyze_structured_data(
            file_path=source_path,
            file_id=str(file_id),
            original_filename=file_record.original_filename,
            format_id=fmt,
            options=options,
        )

        sub_dir = f"structured_{file_id}"
        artifacts: dict[str, str] = {}
        try:
            json_bytes = self.json_generator.generate(doc).encode("utf-8")
            artifacts["json"] = await local_storage.save_file(
                f"{sub_dir}/document.json", json_bytes, folder="processed"
            )
            md_bytes = self.markdown_generator.generate(doc).encode("utf-8")
            artifacts["markdown"] = await local_storage.save_file(
                f"{sub_dir}/structured_analysis.md", md_bytes, folder="processed"
            )
            csv_bytes = self.csv_generator.generate(doc).encode("utf-8")
            if csv_bytes:
                artifacts["csv"] = await local_storage.save_file(
                    f"{sub_dir}/sample_records.csv", csv_bytes, folder="processed"
                )
        except Exception as err:
            logger.warning("Artifact saving error in process_and_persist: %s", err)

        record = StructuredDataAnalysisRecord(
            file_id=file_id,
            status=doc.status,
            format=doc.format,
            root_type=doc.root_type,
            record_count=doc.data_profile.total_rows,
            field_count=doc.data_profile.total_columns,
            max_depth=doc.metadata.get("max_depth", 1),
            is_valid=doc.validation_results.is_valid,
            compression="snappy" if doc.format == "parquet" else "none",
            model_name=doc.model_information.engine_name,
            engine_name="documind-structured",
            confidence=1.0 if doc.validation_results.is_valid else 0.5,
            processing_duration=0.0,
            artifacts=artifacts,
            schema_definition=doc.schema_definition,
            profile_data=doc.data_profile.model_dump(),
            warnings=doc.warnings,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        return doc


structured_pipeline = StructuredDataIntelligencePipeline()
