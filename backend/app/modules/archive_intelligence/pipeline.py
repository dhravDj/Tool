"""Archive Intelligence Pipeline orchestrating inspection, safe extraction, and downstream routing."""

import hashlib
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import FileStatus
from app.infrastructure.database.models import (
    ArchiveAnalysisRecord,
    ArchiveEntryRecord,
    ArchiveRelationshipRecord,
    FileRecord,
)
from app.infrastructure.storage.local import local_storage
from app.modules.archive_intelligence.config import ArchiveSafetyConfig, archive_config
from app.modules.archive_intelligence.extractors.safe_extractor import SafeArchiveExtractor
from app.modules.archive_intelligence.generators.child_manifest_generator import (
    ArchiveChildFileManifestGenerator,
)
from app.modules.archive_intelligence.generators.extraction_report_generator import (
    ArchiveExtractionReportGenerator,
)
from app.modules.archive_intelligence.generators.json_generator import ArchiveJSONGenerator
from app.modules.archive_intelligence.generators.manifest_generator import (
    ArchiveManifestGenerator,
)
from app.modules.archive_intelligence.generators.markdown_generator import (
    ArchiveMarkdownGenerator,
)
from app.modules.archive_intelligence.generators.security_report_generator import (
    ArchiveSecurityReportGenerator,
)
from app.modules.archive_intelligence.generators.text_generator import ArchivePlainTextGenerator
from app.modules.archive_intelligence.generators.tree_generator import ArchiveTreeGenerator
from app.modules.archive_intelligence.hierarchy import ArchiveHierarchyBuilder
from app.modules.archive_intelligence.inspectors.registry import inspector_registry
from app.modules.archive_intelligence.schemas.archive_document import (
    ArchiveDocument,
)
from app.modules.audio_intelligence.pipeline import AudioIntelligencePipeline
from app.modules.code_intelligence.pipeline import CodeIntelligencePipeline
from app.modules.extraction.pipeline import extraction_pipeline
from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.formats.categories import FormatCategory
from app.modules.image_intelligence.pipeline import ImageIntelligencePipeline
from app.modules.presentation_intelligence.pipeline import PresentationIntelligencePipeline
from app.modules.spreadsheet_intelligence.pipeline import SpreadsheetIntelligencePipeline
from app.modules.structured_data_intelligence.pipeline import (
    StructuredDataIntelligencePipeline,
)
from app.modules.video_intelligence.pipeline import VideoIntelligencePipeline

logger = logging.getLogger(__name__)

SUPPORTED_ARCHIVE_FORMATS = [
    "zip",
    "7z",
    "tar",
    "tar.gz",
    "tgz",
    "gz",
    "tar.bz2",
    "tbz2",
    "tar.xz",
    "txz",
]


class ArchiveIntelligencePipeline:
    """Orchestrates archive inspection, isolated extraction, recursive nested handling, and downstream routing."""

    def __init__(self, config: ArchiveSafetyConfig | None = None) -> None:
        self.config = config or archive_config
        self.extractor = SafeArchiveExtractor(self.config)
        self.detector = UniversalFileDetector()

        # Generators
        self.json_generator = ArchiveJSONGenerator()
        self.markdown_generator = ArchiveMarkdownGenerator()
        self.text_generator = ArchivePlainTextGenerator()
        self.manifest_generator = ArchiveManifestGenerator()
        self.tree_generator = ArchiveTreeGenerator()
        self.extraction_report_generator = ArchiveExtractionReportGenerator()
        self.security_report_generator = ArchiveSecurityReportGenerator()
        self.child_manifest_generator = ArchiveChildFileManifestGenerator()

    def get_capabilities(self) -> dict[str, Any]:
        """Expose current system archive intelligence capabilities and safety limits."""
        return {
            "supported_formats": SUPPORTED_ARCHIVE_FORMATS,
            "max_nesting_depth": self.config.max_nesting_depth,
            "max_entries_per_archive": self.config.max_entries_per_archive,
            "max_total_entries_per_job": self.config.max_total_entries_per_job,
            "max_single_file_size_bytes": self.config.max_single_file_size_bytes,
            "max_total_extracted_size_bytes": self.config.max_total_extracted_size_bytes,
            "max_archive_size_bytes": self.config.max_archive_size_bytes,
            "max_path_length": self.config.max_path_length,
            "max_extraction_time_seconds": self.config.max_extraction_time_seconds,
            "max_concurrent_jobs": self.config.max_concurrent_jobs,
            "features": [
                "safe_metadata_inspection",
                "normalized_hierarchy_tree",
                "path_traversal_defense",
                "symlink_escape_blocking",
                "archive_bomb_protection",
                "password_detection",
                "streaming_quota_accounting",
                "recursive_nested_archive_processing",
                "cycle_detection_sha256",
                "downstream_intelligence_routing",
                "provenance_tracking",
            ],
        }

    async def analyze_archive(
        self,
        file_path: Path,
        file_id: str,
        original_filename: str | None = None,
        mode: str = "inspect_only",
        selected_entry_ids: list[str] | None = None,
        password: str | None = None,
        session: AsyncSession | None = None,
        owner_id: uuid.UUID | None = None,
        root_archive_id: str | None = None,
        current_depth: int = 0,
        seen_archive_hashes: set[str] | None = None,
    ) -> ArchiveDocument:
        """Execute archive inspection and optional safe extraction / downstream analysis."""
        start_time = time.monotonic()
        archive_uuid = str(uuid.uuid4())
        actual_root_id = root_archive_id or archive_uuid
        seen_hashes = set(seen_archive_hashes or [])

        # Add this archive's hash to prevent recursion cycles
        try:
            with open(file_path, "rb") as f:
                head_chunk = f.read(65536)
                arc_hash = hashlib.sha256(head_chunk).hexdigest()
                seen_hashes.add(arc_hash)
        except Exception:
            arc_hash = str(file_id)

        # 1. Safe metadata inspection
        metadata, entries, safety_report = inspector_registry.inspect(
            file_path=file_path,
            claimed_format=None,
            max_entries=self.config.max_entries_per_archive,
        )
        metadata["filename"] = original_filename or file_path.name

        # Build directory tree
        hierarchy = ArchiveHierarchyBuilder.build_tree(
            archive_name=metadata["filename"],
            entries=entries,
        )

        extracted_files: list[dict[str, Any]] = []
        blocked_entries: list[dict[str, Any]] = []
        failed_entries: list[dict[str, Any]] = []
        nested_archives: list[dict[str, Any]] = []
        total_extracted_size = 0
        overall_status = "completed"

        if safety_report.encryption_detected:
            overall_status = "password_required"
        if safety_report.corruption_detected:
            overall_status = "partial"

        # Pre-flush ArchiveAnalysisRecord if session present to satisfy child foreign keys
        if session is not None:
            pre_record = ArchiveAnalysisRecord(
                id=uuid.UUID(archive_uuid),
                file_id=uuid.UUID(file_id),
                status="processing",
                archive_format=metadata.get("format", "zip"),
                processing_mode=mode,
                entry_count=len(entries),
                file_count=metadata.get("file_count", 0),
                directory_count=metadata.get("directory_count", 0),
                nested_archive_count=0,
                total_uncompressed_size=metadata.get("total_uncompressed_size", 0),
                extracted_size=0,
                compression_ratio=metadata.get("compression_ratio", 1.0),
                nesting_depth=current_depth,
                is_encrypted=metadata.get("is_encrypted", False),
                is_corrupted=metadata.get("is_corrupted", False),
                archive_comment=metadata.get("comment"),
                model_name="documind-archive-v1",
                engine_name="documind-archive",
                confidence=1.0,
                processing_duration=0.0,
                safety_report=safety_report.model_dump(),
                artifacts={},
                archive_metadata=metadata,
                warnings=safety_report.warnings,
                error_details=None,
            )
            session.add(pre_record)
            await session.flush()

        # 2. Extraction & downstream routing if requested
        if mode in ("extract_only", "extract_and_analyze", "selective"):
            # Isolated directory for extracted output
            extract_dest_rel = f"extracted/{file_id}_{archive_uuid[:8]}"
            extract_dest = local_storage.root / extract_dest_rel
            extract_dest.mkdir(parents=True, exist_ok=True)

            ext_files, blk_entries, fail_entries, ext_safety = self.extractor.extract(
                file_path=file_path,
                dest_root=extract_dest,
                selected_entry_ids=selected_entry_ids if mode == "selective" else None,
                password=password,
            )

            extracted_files.extend(ext_files)
            blocked_entries.extend(blk_entries)
            failed_entries.extend(fail_entries)

            # Merge extraction safety findings
            safety_report.path_traversal_blocked += ext_safety.path_traversal_blocked
            safety_report.symlink_entries_blocked += ext_safety.symlink_entries_blocked
            safety_report.suspicious_entries += ext_safety.suspicious_entries
            safety_report.blocked_entry_count += ext_safety.blocked_entry_count
            if ext_safety.size_limit_exceeded:
                safety_report.size_limit_exceeded = True
            if ext_safety.compression_ratio_exceeded:
                safety_report.compression_ratio_exceeded = True
            if ext_safety.timeout_exceeded:
                safety_report.timeout_exceeded = True
            if ext_safety.encryption_detected:
                safety_report.encryption_detected = True
            if ext_safety.corruption_detected:
                safety_report.corruption_detected = True
            safety_report.warnings.extend(ext_safety.warnings)

            total_extracted_size = sum(f.get("file_size", 0) for f in extracted_files)

            if fail_entries or blocked_entries:
                overall_status = "partial" if extracted_files else "failed"
            if safety_report.compression_ratio_exceeded or safety_report.size_limit_exceeded:
                overall_status = "blocked"

            # Update entry statuses in entries list
            ext_map = {f["entry_id"]: f for f in extracted_files}
            blk_map = {b["entry_id"]: b for b in blocked_entries}
            fail_map = {x["entry_id"]: x for x in failed_entries}

            for entry in entries:
                if entry.entry_id in ext_map:
                    entry.processing_status = "extracted"
                elif entry.entry_id in blk_map:
                    entry.processing_status = "blocked"
                    entry.error = blk_map[entry.entry_id].get("reason")
                elif entry.entry_id in fail_map:
                    entry.processing_status = "failed"
                    entry.error = fail_map[entry.entry_id].get("error")

            # 3. Register child files and route to downstream engines if session available
            if session is not None:
                for f_info in extracted_files:
                    c_path = Path(f_info["extracted_path"])
                    if not c_path.exists():
                        continue

                    # Multi-signal file format detection
                    det = self.detector.detect_file(c_path, original_filename=c_path.name)
                    storage_rel = str(c_path.relative_to(local_storage.root))

                    child_file_id = uuid.uuid4()
                    child_record = FileRecord(
                        id=child_file_id,
                        owner_id=owner_id,
                        original_filename=c_path.name,
                        stored_filename=f"{child_file_id}_{c_path.name}",
                        extension=det.extension or c_path.suffix.lstrip("."),
                        detected_mime_type=det.mime_type,
                        file_size=f_info["file_size"],
                        sha256=f_info["sha256"],
                        storage_path=storage_rel,
                        status=FileStatus.STORED.value,
                        actual_extension=det.extension,
                        detection_format_id=det.format_id,
                        format_category=det.category.value,
                        confidence_score=det.confidence_score,
                    )
                    session.add(child_record)
                    await session.flush()

                    f_info["created_file_id"] = str(child_file_id)

                    # Create provenance relationship record
                    rel_record = ArchiveRelationshipRecord(
                        parent_file_id=uuid.UUID(file_id),
                        parent_archive_id=uuid.UUID(archive_uuid),
                        parent_entry_id=f_info["entry_id"],
                        child_file_id=child_file_id,
                        root_archive_id=uuid.UUID(actual_root_id),
                        nesting_depth=current_depth + 1,
                        original_path=f_info["original_path"],
                        extracted_storage_reference=storage_rel,
                        sha256=f_info["sha256"],
                        detection_result={
                            "format_id": det.format_id,
                            "category": det.category.value,
                            "mime_type": det.mime_type,
                        },
                        processing_status="extracted",
                    )
                    session.add(rel_record)
                    await session.flush()

                    # Downstream routing if mode == extract_and_analyze
                    if mode in ("extract_and_analyze", "selective"):
                        downstream_engine = None
                        try:
                            # 1. Nested Archive
                            if (
                                f_info.get("is_nested_archive")
                                and (current_depth + 1) < self.config.max_nesting_depth
                            ):
                                if f_info["sha256"] in seen_hashes:
                                    safety_report.warnings.append(
                                        f"Cycle/duplicate detected on nested archive '{c_path.name}'; skipped recursion."
                                    )
                                else:
                                    downstream_engine = "archive_intelligence"
                                    nested_doc = await self.analyze_archive(
                                        file_path=c_path,
                                        file_id=str(child_file_id),
                                        original_filename=c_path.name,
                                        mode=mode,
                                        session=session,
                                        owner_id=owner_id,
                                        root_archive_id=actual_root_id,
                                        current_depth=current_depth + 1,
                                        seen_archive_hashes=seen_hashes,
                                    )
                                    nested_archives.append(
                                        {
                                            "archive_id": nested_doc.archive_id,
                                            "filename": c_path.name,
                                            "depth": current_depth + 1,
                                            "entry_count": nested_doc.total_entry_count,
                                            "extracted_size": nested_doc.extracted_size,
                                        }
                                    )
                            # 2. Documents (PDF, DOCX, TXT, MD, RTF, ODT, EPUB)
                            elif det.category in (FormatCategory.DOCUMENT, FormatCategory.PDF):
                                downstream_engine = "document_extraction"
                                await extraction_pipeline.extract(
                                    file_id=child_file_id, session=session
                                )
                            # 3. Images
                            elif det.category == FormatCategory.IMAGE:
                                downstream_engine = "image_intelligence"
                                img_pipe = ImageIntelligencePipeline()
                                await img_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 4. Spreadsheets
                            elif det.category == FormatCategory.SPREADSHEET:
                                downstream_engine = "spreadsheet_intelligence"
                                sheet_pipe = SpreadsheetIntelligencePipeline()
                                await sheet_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 5. Presentations
                            elif det.category == FormatCategory.PRESENTATION:
                                downstream_engine = "presentation_intelligence"
                                pres_pipe = PresentationIntelligencePipeline()
                                await pres_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 6. Audio
                            elif det.category == FormatCategory.AUDIO:
                                downstream_engine = "audio_intelligence"
                                aud_pipe = AudioIntelligencePipeline()
                                await aud_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 7. Video
                            elif det.category == FormatCategory.VIDEO:
                                downstream_engine = "video_intelligence"
                                vid_pipe = VideoIntelligencePipeline()
                                await vid_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 8. Code
                            elif det.category == FormatCategory.CODE:
                                downstream_engine = "code_intelligence"
                                code_pipe = CodeIntelligencePipeline()
                                await code_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )
                            # 9. Structured Data
                            elif det.category == FormatCategory.STRUCTURED_DATA:
                                downstream_engine = "structured_data_intelligence"
                                data_pipe = StructuredDataIntelligencePipeline()
                                await data_pipe.process_and_persist(
                                    file_id=child_file_id, session=session
                                )

                            if downstream_engine:
                                f_info["downstream_engine"] = downstream_engine
                                rel_record.processing_status = "analyzed"
                                await session.flush()

                        except Exception as e:
                            logger.warning(
                                "Downstream routing error for file %s with engine %s: %s",
                                c_path.name,
                                downstream_engine,
                                e,
                            )
                            safety_report.warnings.append(
                                f"Downstream analysis failed for '{c_path.name}' ({downstream_engine}): {e}"
                            )

        elapsed = time.monotonic() - start_time

        doc = ArchiveDocument(
            archive_id=archive_uuid,
            source_file_id=file_id,
            archive_format=metadata.get("format", "zip"),
            metadata=metadata,
            entries=entries,
            hierarchy=hierarchy,
            nested_archives=nested_archives,
            extracted_files=extracted_files,
            blocked_entries=blocked_entries,
            failed_entries=failed_entries,
            processing_mode=mode,
            processing_status=overall_status,
            extracted_size=total_extracted_size,
            total_entry_count=len(entries),
            nesting_depth=current_depth,
            safety_report=safety_report,
            processing_metadata={
                "duration": round(elapsed, 3),
                "engine": "documind-archive-engine",
                "version": "1.0.0",
            },
            warnings=list(dict.fromkeys(safety_report.warnings)),
            errors=[],
        )

        return doc

    async def process_and_persist(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        mode: str = "inspect_only",
        selected_entry_ids: list[str] | None = None,
        password: str | None = None,
        root_archive_id: str | None = None,
        current_depth: int = 0,
        seen_archive_hashes: set[str] | None = None,
    ) -> ArchiveDocument:
        """Inspect, extract, persist database records, and save artifacts."""
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        file_record = res.scalar_one_or_none()
        if not file_record:
            raise FileNotFoundError(f"FileRecord with ID {file_id} not found.")

        resolved = local_storage.get_local_path(file_record.storage_path)
        source_path = resolved if resolved is not None else Path(file_record.storage_path)

        doc = await self.analyze_archive(
            file_path=source_path,
            file_id=str(file_id),
            original_filename=file_record.original_filename,
            mode=mode,
            selected_entry_ids=selected_entry_ids,
            password=password,
            session=session,
            owner_id=file_record.owner_id,
            root_archive_id=root_archive_id,
            current_depth=current_depth,
            seen_archive_hashes=seen_archive_hashes,
        )

        sub_dir = f"archive_{file_id}"
        artifacts: dict[str, str] = {}
        try:
            # 1. JSON
            artifacts["json"] = await local_storage.save_file(
                f"{sub_dir}/archive_document.json",
                self.json_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
            # 2. Markdown
            artifacts["markdown"] = await local_storage.save_file(
                f"{sub_dir}/archive_report.md",
                self.markdown_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
            # 3. Plain Text
            artifacts["text"] = await local_storage.save_file(
                f"{sub_dir}/archive_summary.txt",
                self.text_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
            # 4. Manifest
            artifacts["manifest"] = await local_storage.save_file(
                f"{sub_dir}/manifest.json",
                self.manifest_generator.generate(doc, "json").encode("utf-8"),
                folder="processed",
            )
            # 5. Tree
            artifacts["tree"] = await local_storage.save_file(
                f"{sub_dir}/hierarchy_tree.txt",
                self.tree_generator.generate(doc.hierarchy).encode("utf-8"),
                folder="processed",
            )
            # 6. Extraction Report
            artifacts["extraction_report"] = await local_storage.save_file(
                f"{sub_dir}/extraction_report.json",
                self.extraction_report_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
            # 7. Security Report
            artifacts["security_report"] = await local_storage.save_file(
                f"{sub_dir}/security_report.json",
                self.security_report_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
            # 8. Child Manifest
            artifacts["child_manifest"] = await local_storage.save_file(
                f"{sub_dir}/child_manifest.json",
                self.child_manifest_generator.generate(doc).encode("utf-8"),
                folder="processed",
            )
        except Exception as err:
            logger.warning("Artifact saving error in archive process_and_persist: %s", err)

        # Update existing flushed ArchiveAnalysisRecord or insert if missing
        analysis_record = await session.get(ArchiveAnalysisRecord, uuid.UUID(doc.archive_id))
        meta = doc.metadata
        if analysis_record:
            analysis_record.status = doc.processing_status
            analysis_record.extracted_size = doc.extracted_size
            analysis_record.nested_archive_count = len(doc.nested_archives)
            analysis_record.processing_duration = doc.processing_metadata.get("duration", 0.0)
            analysis_record.safety_report = doc.safety_report.model_dump()
            analysis_record.artifacts = artifacts
            analysis_record.archive_metadata = meta
            analysis_record.warnings = doc.warnings
            analysis_record.error_details = doc.errors[0] if doc.errors else None
        else:
            analysis_record = ArchiveAnalysisRecord(
                id=uuid.UUID(doc.archive_id),
                file_id=file_id,
                status=doc.processing_status,
                archive_format=doc.archive_format,
                processing_mode=doc.processing_mode,
                entry_count=doc.total_entry_count,
                file_count=meta.get("file_count", 0),
                directory_count=meta.get("directory_count", 0),
                nested_archive_count=len(doc.nested_archives),
                total_uncompressed_size=meta.get("total_uncompressed_size", 0),
                extracted_size=doc.extracted_size,
                compression_ratio=meta.get("compression_ratio", 1.0),
                nesting_depth=doc.nesting_depth,
                is_encrypted=meta.get("is_encrypted", False),
                is_corrupted=meta.get("is_corrupted", False),
                archive_comment=meta.get("comment"),
                model_name="documind-archive-v1",
                engine_name="documind-archive",
                confidence=1.0,
                processing_duration=doc.processing_metadata.get("duration", 0.0),
                safety_report=doc.safety_report.model_dump(),
                artifacts=artifacts,
                archive_metadata=meta,
                warnings=doc.warnings,
                error_details=doc.errors[0] if doc.errors else None,
            )
            session.add(analysis_record)
        await session.flush()

        # Add ArchiveEntryRecords
        for entry in doc.entries:
            entry_rec = ArchiveEntryRecord(
                archive_analysis_id=analysis_record.id,
                entry_id=entry.entry_id,
                original_path=entry.original_path,
                normalized_path=entry.normalized_path,
                filename=entry.filename,
                extension=entry.extension,
                entry_type=entry.entry_type,
                compressed_size=entry.compressed_size,
                uncompressed_size=entry.uncompressed_size,
                compression_method=entry.compression_method,
                checksum=entry.checksum,
                encrypted=entry.encrypted,
                is_directory=entry.is_directory,
                is_symlink=entry.is_symlink,
                is_nested_archive=entry.is_nested_archive,
                detection_result=entry.detection_result,
                extracted_file_id=uuid.UUID(entry.extracted_file_id)
                if entry.extracted_file_id
                else None,
                processing_status=entry.processing_status,
                error=entry.error,
            )
            session.add(entry_rec)

        await session.commit()
        return doc


archive_pipeline = ArchiveIntelligencePipeline()
