"""Code Intelligence Pipeline orchestrating language parsers, metrics, and diagnostics."""

import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import CodeAnalysisRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.code_intelligence.generators.json_generator import CodeJSONGenerator
from app.modules.code_intelligence.generators.markdown_generator import CodeMarkdownGenerator
from app.modules.code_intelligence.generators.text_generator import CodePlainTextGenerator
from app.modules.code_intelligence.parsers.registry import language_parser_registry
from app.modules.code_intelligence.schemas.code_document import (
    CodeDocument,
    CodeModelInfo,
)

logger = logging.getLogger(__name__)

SUPPORTED_CODE_LANGUAGES = ["py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"]


class CodeIntelligenceError(Exception):
    """Base exception for code intelligence errors."""


class UnsupportedLanguageError(CodeIntelligenceError):
    """Raised when an unhandled programming language is encountered."""


class CodeIntelligencePipeline:
    """Orchestrates multi-language code parsing, symbol extraction, static diagnostics, and metrics."""

    def __init__(self) -> None:
        self.parser_registry = language_parser_registry
        self.json_generator = CodeJSONGenerator()
        self.markdown_generator = CodeMarkdownGenerator()
        self.text_generator = CodePlainTextGenerator()

    def get_capabilities(self) -> dict[str, Any]:
        """Expose current system code intelligence capabilities."""
        return {
            "supported_languages": SUPPORTED_CODE_LANGUAGES,
            "installed_parsers": [p["class"] for p in self.parser_registry.list_supported_languages()],
            "features": [
                "symbol_extraction",
                "import_dependency_analysis",
                "static_code_diagnostics",
                "security_vulnerability_detection",
                "cyclomatic_complexity",
                "line_metrics",
                "sql_schema_extraction",
            ],
            "max_file_size_bytes": getattr(settings, "MAX_CODE_FILE_SIZE", 50 * 1024 * 1024),
        }

    async def analyze_code(
        self,
        file_path: Path | str,
        file_id: str,
        original_filename: str = "",
        language: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> CodeDocument:
        """Perform end-to-end code intelligence analysis on the given local source file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found at: {path}")

        filename = original_filename or path.name

        # Resolve parser
        parser = None
        if language:
            parser = self.parser_registry.get_parser_for_language(language)
        if not parser:
            parser = self.parser_registry.get_parser_for_filename(filename)

        if not parser:
            raise UnsupportedLanguageError(f"Unsupported programming language or extension for file: '{filename}'")

        # Read content safely
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as read_err:
            raise CodeIntelligenceError(f"Failed to read source file '{filename}': {read_err}") from read_err

        # Parse
        symbols, imports, dependencies, metrics, diagnostics, syntax_val = parser.parse(
            content=content,
            filename=filename,
            options=options,
        )

        ext = filename.split(".")[-1].lower() if "." in filename else ""
        doc_language = language or (ext if ext in SUPPORTED_CODE_LANGUAGES else parser.language)

        doc = CodeDocument(
            document_id=f"code_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            language=doc_language,
            encoding="utf-8",
            file_metadata={
                "filename": filename,
                "file_size": path.stat().st_size,
                "line_count": metrics.total_lines,
            },
            symbols=symbols,
            imports=imports,
            dependencies=dependencies,
            metrics=metrics,
            diagnostics=diagnostics,
            syntax_validation=syntax_val,
            source_references=[f"L{s.start_line}: {s.name}" for s in symbols[:20]],
            processing_metadata={
                "parser_class": parser.__class__.__name__,
            },
            model_information=CodeModelInfo(
                engine_name="documind-code-v1",
                parser_type=parser.__class__.__name__,
                is_compiler=False,
                capabilities=["ast_parsing", "static_heuristics", "metrics"],
            ),
            warnings=[d.message for d in diagnostics if d.severity in ("warning", "error")],
            status="completed" if syntax_val.is_valid else "syntax_error",
            source_code=content,
        )

        # Persist generated artifacts asynchronously
        try:
            json_str = self.json_generator.generate(doc)
            md_str = self.markdown_generator.generate(doc)
            txt_str = self.text_generator.generate(doc)

            await local_storage.save_file(
                f"code/{file_id}/code_document.json",
                json_str.encode("utf-8"),
            )
            await local_storage.save_file(
                f"code/{file_id}/code_analysis.md",
                md_str.encode("utf-8"),
            )
            await local_storage.save_file(
                f"code/{file_id}/code_summary.txt",
                txt_str.encode("utf-8"),
            )
        except Exception as save_err:
            logger.warning("Failed to persist code artifacts for %s: %s", file_id, save_err)

        return doc

    async def process_and_persist(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> CodeDocument:
        """Analyze code for a registered FileRecord, persist artifacts and CodeAnalysisRecord."""
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        file_record = res.scalar_one_or_none()
        if not file_record:
            raise FileNotFoundError(f"FileRecord with ID {file_id} not found.")

        resolved = local_storage.get_local_path(file_record.storage_path)
        source_path = resolved if resolved is not None else Path(file_record.storage_path)
        lang = (file_record.detection_format_id or file_record.actual_extension or "").lower()

        doc = await self.analyze_code(
            file_path=source_path,
            file_id=str(file_id),
            original_filename=file_record.original_filename,
            language=lang,
            options=options,
        )

        sub_dir = f"code_{file_id}"
        artifacts: dict[str, str] = {}
        try:
            json_bytes = self.json_generator.generate(doc).encode("utf-8")
            artifacts["json"] = await local_storage.save_file(
                f"{sub_dir}/document.json", json_bytes, folder="processed"
            )
            md_bytes = self.markdown_generator.generate(doc).encode("utf-8")
            artifacts["markdown"] = await local_storage.save_file(
                f"{sub_dir}/code_analysis.md", md_bytes, folder="processed"
            )
        except Exception as err:
            logger.warning("Artifact saving error in process_and_persist: %s", err)

        record = CodeAnalysisRecord(
            file_id=file_id,
            status=doc.status,
            language=doc.language,
            total_lines=doc.metrics.total_lines,
            code_lines=doc.metrics.code_lines,
            comment_lines=doc.metrics.comment_lines,
            blank_lines=doc.metrics.blank_lines,
            symbol_count=len(doc.symbols),
            function_count=doc.metrics.function_count,
            class_count=doc.metrics.class_count,
            import_count=len(doc.imports),
            diagnostic_count=len(doc.diagnostics),
            has_syntax_errors=not doc.syntax_validation.is_valid,
            cyclomatic_complexity=doc.metrics.cyclomatic_complexity,
            model_name=doc.model_information.engine_name,
            engine_name="documind-code",
            confidence=1.0 if doc.syntax_validation.is_valid else 0.5,
            processing_duration=0.0,
            artifacts=artifacts,
            code_metadata=doc.file_metadata,
            warnings=doc.warnings,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        return doc


code_pipeline = CodeIntelligencePipeline()
