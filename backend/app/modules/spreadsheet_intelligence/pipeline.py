"""Spreadsheet Intelligence Pipeline Orchestrator."""

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import FileRecord, SpreadsheetAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.spreadsheet_intelligence.adapters.base import BaseSpreadsheetAdapter
from app.modules.spreadsheet_intelligence.adapters.delimited import DelimitedSpreadsheetAdapter
from app.modules.spreadsheet_intelligence.adapters.ods import ODSAdapter
from app.modules.spreadsheet_intelligence.adapters.xls import LegacyXLSAdapter
from app.modules.spreadsheet_intelligence.adapters.xlsx import XLSXAdapter
from app.modules.spreadsheet_intelligence.generators.csv_exporter import SpreadsheetCSVExporter
from app.modules.spreadsheet_intelligence.generators.json_generator import SpreadsheetJSONGenerator
from app.modules.spreadsheet_intelligence.generators.manifest_generator import (
    SpreadsheetManifestGenerator,
)
from app.modules.spreadsheet_intelligence.generators.markdown_generator import (
    SpreadsheetMarkdownGenerator,
)
from app.modules.spreadsheet_intelligence.generators.parquet_exporter import (
    SpreadsheetParquetExporter,
)
from app.modules.spreadsheet_intelligence.generators.xlsx_exporter import (
    SpreadsheetXLSXExporter,
)
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
    SpreadsheetManifest,
)

logger = logging.getLogger(__name__)


class UnsupportedSpreadsheetFormatError(Exception):
    """Raised when an unhandled format is passed to spreadsheet intelligence."""
    pass


class SpreadsheetIntelligencePipeline:
    """Orchestrates format routing, extraction, profiling, artifact creation, and persistence."""

    def __init__(self) -> None:
        self.adapters: dict[str, BaseSpreadsheetAdapter] = {
            "xlsx": XLSXAdapter(),
            "xls": LegacyXLSAdapter(),
            "csv": DelimitedSpreadsheetAdapter(default_delimiter=","),
            "tsv": DelimitedSpreadsheetAdapter(default_delimiter="\t"),
            "ods": ODSAdapter(),
        }

    def list_supported_formats(self) -> list[str]:
        return sorted(self.adapters.keys())

    def get_adapter(self, format_id: str) -> BaseSpreadsheetAdapter:
        fmt = format_id.lower().strip()
        adapter = self.adapters.get(fmt)
        if not adapter:
            raise UnsupportedSpreadsheetFormatError(
                f"Unsupported spreadsheet format '{format_id}'. Supported formats: {self.list_supported_formats()}"
            )
        return adapter

    def extract_document(
        self,
        file_path: Path,
        format_id: str,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> SpreadsheetDocument:
        """Extract canonical spreadsheet document using matching format adapter."""
        adapter = self.get_adapter(format_id)
        return adapter.extract_workbook(
            file_path=file_path,
            original_filename=original_filename,
            options=options,
        )

    async def analyze_file_record(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> tuple[SpreadsheetDocument, SpreadsheetManifest]:
        """Execute end-to-end spreadsheet intelligence for an ingested FileRecord."""
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
            or "csv"
        ).lower()

        # Resolve path
        file_path = local_storage._resolve_safe_path(record.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Storage path {record.storage_path} does not exist.")

        # Execute extraction
        doc = self.extract_document(
            file_path=file_path,
            format_id=fmt,
            original_filename=record.original_filename,
            options={"file_id": str(file_id), **opts},
        )

        # Generate and save artifacts
        artifacts: dict[str, str] = {}
        storage_folder = f"processed/{file_id}/spreadsheet"

        # 1. JSON
        json_str = SpreadsheetJSONGenerator.generate(doc)
        json_path = await local_storage.save_file(
            destination_key="spreadsheet_document.json",
            content=json_str.encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["json"] = json_path

        # 2. Markdown
        md_str = SpreadsheetMarkdownGenerator.generate(doc)
        md_path = await local_storage.save_file(
            destination_key="spreadsheet_report.md",
            content=md_str.encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["markdown"] = md_path

        # 3. CSV per worksheet
        for ws in doc.worksheets:
            sheet_csv = SpreadsheetCSVExporter.export_sheet_csv(ws, sanitize_formulas=True)
            safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in ws.name)
            csv_path = await local_storage.save_file(
                destination_key=f"worksheet_{ws.position}_{safe_name}.csv",
                content=sheet_csv.encode("utf-8"),
                folder=storage_folder,
            )
            artifacts[f"csv_sheet_{ws.position}"] = csv_path

        # 4. Reconstructed XLSX export
        try:
            xlsx_bytes = SpreadsheetXLSXExporter.export_workbook(doc)
            xlsx_path = await local_storage.save_file(
                destination_key="spreadsheet_export.xlsx",
                content=xlsx_bytes,
                folder=storage_folder,
            )
            artifacts["xlsx"] = xlsx_path
        except Exception as e:
            logger.warning(f"Could not generate reconstructed XLSX: {e}")

        # 5. Optional Parquet for primary sheet
        if SpreadsheetParquetExporter.is_available() and doc.worksheets:
            try:
                parquet_bytes = SpreadsheetParquetExporter.export_sheet_parquet(doc.worksheets[0])
                if parquet_bytes:
                    pq_path = await local_storage.save_file(
                        destination_key="worksheet_1.parquet",
                        content=parquet_bytes,
                        folder=storage_folder,
                    )
                    artifacts["parquet_sheet_1"] = pq_path
            except Exception as e:
                logger.debug(f"Parquet export skipped: {e}")

        duration = time.monotonic() - start_time

        # 6. Manifest
        adapter = self.get_adapter(fmt)
        manifest = SpreadsheetManifestGenerator.generate(
            doc=doc,
            status="completed",
            engine_name=adapter.engine_name,
            engine_version=adapter.version,
            duration_seconds=duration,
            artifacts=artifacts,
        )
        manifest_path = await local_storage.save_file(
            destination_key="spreadsheet_manifest.json",
            content=manifest.model_dump_json(indent=2).encode("utf-8"),
            folder=storage_folder,
        )
        artifacts["manifest"] = manifest_path

        # 7. Persist to PostgreSQL database
        total_rows = sum(ws.total_rows for ws in doc.worksheets)
        total_cols = sum(ws.total_columns for ws in doc.worksheets)
        total_cells = sum(sum(len(r.cells) for r in ws.rows) for ws in doc.worksheets)
        total_formulas = sum(
            sum(sum(1 for c in r.cells if c.formula) for r in ws.rows)
            for ws in doc.worksheets
        )
        has_charts = any(len(ws.charts) > 0 for ws in doc.worksheets)
        has_tables = any(len(ws.tables) > 0 for ws in doc.worksheets)
        has_merged = any(len(ws.merged_ranges) > 0 for ws in doc.worksheets)
        has_hidden = any(ws.visibility != "visible" for ws in doc.worksheets)

        # Build profiling summary
        profiling_dict = {}
        if doc.worksheets and doc.worksheets[0].profiling:
            p = doc.worksheets[0].profiling
            profiling_dict = {
                "candidate_primary_keys": p.candidate_primary_keys,
                "empty_rows_count": p.empty_rows_count,
                "duplicate_rows_count": p.duplicate_rows_count,
                "columns_profiled": len(p.column_profiles),
            }

        analysis_record = SpreadsheetAnalysisRecord(
            file_id=file_id,
            status="completed",
            format=fmt,
            sheet_count=len(doc.worksheets),
            total_rows=total_rows,
            total_columns=total_cols,
            total_cells=total_cells,
            formula_count=total_formulas,
            has_charts=has_charts,
            has_tables=has_tables,
            has_merged_cells=has_merged,
            has_hidden_sheets=has_hidden,
            artifacts=artifacts,
            workbook_metadata=doc.workbook_metadata.model_dump(),
            profiling_summary=profiling_dict,
            warnings=doc.warnings,
        )
        session.add(analysis_record)
        await session.commit()
        await session.refresh(analysis_record)

        return doc, manifest


# Global pipeline singleton
spreadsheet_pipeline = SpreadsheetIntelligencePipeline()
