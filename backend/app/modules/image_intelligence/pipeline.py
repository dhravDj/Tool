"""Central Image & Visual Intelligence Pipeline Orchestrator."""

import json
import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.domain.enums import FileStatus
from app.infrastructure.database.models import FileRecord, ImageAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.image_intelligence.charts.analyzer import ChartAnalyzer
from app.modules.image_intelligence.diagrams.analyzer import DiagramAnalyzer
from app.modules.image_intelligence.generators.canonical_json import ImageJSONGenerator
from app.modules.image_intelligence.generators.manifest import ImageManifestGenerator
from app.modules.image_intelligence.generators.markdown_report import ImageMarkdownGenerator
from app.modules.image_intelligence.generators.ocr_exporter import ImageOCRExporter
from app.modules.image_intelligence.metadata.extractor import ImageMetadataExtractor
from app.modules.image_intelligence.ocr.engine import ImageOCREngine
from app.modules.image_intelligence.preprocessing.pipeline import ImagePreprocessor
from app.modules.image_intelligence.schemas.image_document import (
    ImageAnalysis,
    ImageAskResponse,
    ImageDocument,
    ImageManifest,
    ImageMetadata,
    VisionModelCapabilities,
)
from app.modules.image_intelligence.vision.engine import VisionIntelligenceEngine
from app.plugins.interfaces.base import PluginMetadata, PluginType, ProcessingPluginInterface


class ImageIntelligencePipeline(ProcessingPluginInterface):
    """Universal Image and Visual Intelligence processing engine."""

    def __init__(self) -> None:
        self.metadata_extractor = ImageMetadataExtractor()
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = ImageOCREngine()
        self.vision_engine = VisionIntelligenceEngine()
        self.diagram_analyzer = DiagramAnalyzer()
        self.chart_analyzer = ChartAnalyzer()

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="image_intelligence_pipeline",
            version="1.0.0",
            description="Universal Image & Visual Intelligence pipeline supporting OCR, Vision Understanding, Charts, and Diagrams.",
            plugin_type=PluginType.EXTRACTOR,
            supported_formats=["png", "jpeg", "jpg", "webp", "tiff", "bmp", "svg"],
            required_dependencies=["pillow", "numpy"],
            hardware_acceleration="cpu",
            author="DocuMind AI Architecture Team",
            is_available=True,
        )

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        logger.info("ImageIntelligencePipeline initialized successfully.")

    async def shutdown(self) -> None:
        pass

    async def check_health(self) -> bool:
        return True

    def get_capabilities(self) -> VisionModelCapabilities:
        """Return platform vision and image processing capabilities."""
        return VisionModelCapabilities(
            supported_formats=["png", "jpeg", "jpg", "webp", "tiff", "bmp", "svg"],
            ocr_engine=self.ocr_engine.tesseract_cmd and "tesseract" or "none",
            ocr_available=self.ocr_engine.is_available,
            default_vision_engine=self.vision_engine.model_name,
            available_vision_engines=[self.vision_engine.model_name, "gemini-flash-vision"],
            hardware_acceleration="cpu",
            max_image_dimension_px=4096,
            privacy_gps_scrubbing=True,
            preprocessing_steps=[
                "exif_orientation_correction",
                "color_normalization_to_rgb",
                "rescale_bounds_check",
                "deskew_angle_correction",
                "grayscale_contrast_enhancement",
                "otsu_binarization",
                "large_image_tiling",
            ],
        )

    async def analyze_file_record(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> tuple[ImageDocument, ImageManifest]:
        """Execute end-to-end image intelligence pipeline on a file record."""
        options = options or {}
        start_time = time.perf_counter()

        # 1. Fetch file record
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ProcessingError(f"File record with ID '{file_id}' not found.")

        local_path = local_storage.get_local_path(record.storage_path)
        if not local_path or not local_path.exists():
            raise ProcessingError(
                f"Underlying file not found at storage path: {record.storage_path}"
            )

        format_id = record.detection_format_id or record.extension.lstrip(".")
        filename = record.original_filename

        # Execute processing
        image_doc, manifest = self.process_image_path(
            file_path=local_path,
            file_id=str(file_id),
            filename=filename,
            format_id=format_id,
            options=options,
        )

        # 2. Persist output artifacts to storage/processed/{file_id}/image/
        dest_dir = f"processed/{file_id}/image"
        json_path = await local_storage.save_file(
            f"{dest_dir}/image_document.json",
            ImageJSONGenerator.generate(image_doc).encode("utf-8"),
            folder="",
        )
        md_path = await local_storage.save_file(
            f"{dest_dir}/image_report.md",
            ImageMarkdownGenerator.generate(image_doc).encode("utf-8"),
            folder="",
        )
        manifest_path = await local_storage.save_file(
            f"{dest_dir}/image_manifest.json",
            json.dumps(manifest.model_dump(), indent=2).encode("utf-8"),
            folder="",
        )
        ocr_text_path = await local_storage.save_file(
            f"{dest_dir}/ocr_text.txt",
            ImageOCRExporter.export(image_doc).encode("utf-8"),
            folder="",
        )

        artifacts = {
            "image_document_json": json_path,
            "image_report_markdown": md_path,
            "image_manifest": manifest_path,
            "ocr_text": ocr_text_path,
        }
        manifest.artifacts = artifacts

        # 3. Record in database (ImageAnalysisRecord)
        analysis_record = ImageAnalysisRecord(
            id=uuid.uuid4(),
            file_id=file_id,
            status=manifest.status,
            format=image_doc.metadata.format,
            width=image_doc.metadata.width,
            height=image_doc.metadata.height,
            color_mode=image_doc.metadata.color_mode,
            has_transparency=image_doc.metadata.has_transparency,
            is_animated=image_doc.metadata.is_animated,
            ocr_word_count=image_doc.analysis.ocr_word_count,
            ocr_text=image_doc.analysis.ocr_full_text or None,
            detected_objects_count=len(image_doc.analysis.detected_objects),
            caption=image_doc.analysis.caption or None,
            has_charts=image_doc.analysis.chart.is_chart,
            has_diagrams=image_doc.analysis.diagram.is_diagram,
            artifacts=artifacts,
            analysis_metadata=image_doc.model_dump(exclude={"regions"}),
        )
        session.add(analysis_record)

        # Update file record status
        record.status = FileStatus.PROCESSED.value
        await session.commit()

        logger.info(
            f"Image intelligence analysis completed for {file_id} in {time.perf_counter() - start_time:.3f}s"
        )
        return image_doc, manifest

    def process_image_path(
        self,
        file_path: Path,
        file_id: str,
        filename: str,
        format_id: str,
        options: dict[str, Any] | None = None,
    ) -> tuple[ImageDocument, ImageManifest]:
        """Synchronously process an image file path through all visual intelligence stages."""
        options = options or {}
        start_time = time.perf_counter()
        image_id = uuid.uuid4().hex
        warnings: list[str] = []
        errors: list[str] = []

        # Stage 1: Technical & Privacy Metadata
        meta: ImageMetadata = self.metadata_extractor.extract(file_path, format_id)

        # Stage 2: Preprocessing (for raster images)
        working_img: Image.Image
        ocr_img: Image.Image
        preprocessed_info: dict[str, str] = {}

        if format_id.lower() == "svg":
            # For SVG, create lightweight raster proxy for vision & OCR
            working_img = Image.new("RGB", (meta.width, meta.height), color="white")
            ocr_img = working_img.copy()
            preprocessed_info["pipeline"] = "vector_svg_xml_analysis"
        else:
            bundle = self.preprocessor.process(
                source=file_path,
                enable_deskew=options.get("enable_deskew", True),
                enable_binarization=options.get("enable_binarization", True),
                enable_contrast_enhancement=options.get("enable_contrast", True),
                enable_tiling=options.get("enable_tiling", True),
            )
            working_img = bundle.working_image
            ocr_img = bundle.ocr_image
            preprocessed_info["steps"] = ", ".join(bundle.applied_steps)
            preprocessed_info["deskew_angle"] = str(bundle.deskew_angle)

        # Stage 3: OCR Subsystem
        text_regions, ocr_text, ocr_conf, ocr_warnings = self.ocr_engine.extract_regions(
            ocr_img, options=options
        )
        warnings.extend(ocr_warnings)

        # Stage 4: Vision Scene Understanding & Objects
        caption, scene_type, objects, dominant_colors, object_regions = (
            self.vision_engine.analyze_scene(
                working_img,
                ocr_text=ocr_text,
                metadata_dict=meta.model_dump(),
            )
        )

        # Stage 5: Diagram & Flowchart Analysis
        diagram_analysis, diagram_regions = self.diagram_analyzer.analyze(
            working_img,
            ocr_text=ocr_text,
            regions=text_regions,
        )

        # Stage 6: Statistical Chart Analysis
        chart_analysis, chart_regions = self.chart_analyzer.analyze(
            working_img,
            ocr_text=ocr_text,
            regions=text_regions,
        )

        # Stage 7: Assemble Consolidated Canonical ImageDocument
        all_regions = text_regions + object_regions + diagram_regions + chart_regions

        analysis = ImageAnalysis(
            caption=caption,
            scene_type=scene_type,
            detected_objects=objects,
            dominant_colors=dominant_colors,
            diagram=diagram_analysis,
            chart=chart_analysis,
            ocr_full_text=ocr_text,
            ocr_word_count=len(ocr_text.split()),
            ocr_average_confidence=ocr_conf,
        )

        status_str = "completed_with_warnings" if warnings else "completed"

        image_doc = ImageDocument(
            image_id=image_id,
            file_id=file_id,
            filename=filename,
            metadata=meta,
            analysis=analysis,
            regions=all_regions,
            preprocessed_artifacts=preprocessed_info,
            warnings=warnings,
        )

        duration = time.perf_counter() - start_time
        manifest = ImageManifestGenerator.create_manifest(
            image_id=image_id,
            file_id=file_id,
            filename=filename,
            status=status_str,
            processing_time_seconds=duration,
            engines_used={
                "metadata": "ImageMetadataExtractor",
                "preprocessing": "ImagePreprocessor",
                "ocr": self.ocr_engine.is_available and "Tesseract" or "none",
                "vision": self.vision_engine.model_name,
                "diagram": "DiagramAnalyzer",
                "chart": "ChartAnalyzer",
            },
            artifacts={},
            warnings=warnings,
            errors=errors,
        )

        return image_doc, manifest

    async def ask_image_question(
        self,
        file_id: uuid.UUID,
        question: str,
        session: AsyncSession,
    ) -> ImageAskResponse:
        """Process an interactive Visual Question Answering (VQA) query."""
        # 1. Fetch latest image analysis record
        stmt = (
            select(ImageAnalysisRecord)
            .where(ImageAnalysisRecord.file_id == file_id)
            .order_by(desc(ImageAnalysisRecord.created_at))
            .limit(1)
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            raise ProcessingError(
                f"No image analysis record found for file '{file_id}'. Run analyze-image first."
            )

        # Read canonical document JSON from storage
        artifacts = record.artifacts or {}
        doc_path = artifacts.get("image_document_json")
        if not doc_path:
            raise ProcessingError("Image document artifact not found in storage.")

        raw_bytes = await local_storage.read_file(doc_path)
        doc_dict = json.loads(raw_bytes.decode("utf-8"))
        image_doc = ImageDocument(**doc_dict)

        # Fetch working image
        file_record = await session.get(FileRecord, file_id)
        local_path = local_storage.get_local_path(file_record.storage_path) if file_record else None
        if not local_path or not local_path.exists():
            raise ProcessingError("Source image file missing from storage.")

        with Image.open(local_path) as img:
            return self.vision_engine.answer_question(
                img=img,
                question=question,
                caption=image_doc.analysis.caption,
                ocr_text=image_doc.analysis.ocr_full_text,
                regions=image_doc.regions,
                diagram_info=image_doc.analysis.diagram.model_dump(),
                chart_info=image_doc.analysis.chart.model_dump(),
            )


# Global singleton instance
image_intelligence_pipeline = ImageIntelligencePipeline()
