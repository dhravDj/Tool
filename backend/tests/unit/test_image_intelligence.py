"""Unit tests for DocuMind AI Image & Visual Intelligence Engine."""

from pathlib import Path

import pytest
from PIL import Image

from app.modules.image_intelligence.charts.analyzer import ChartAnalyzer
from app.modules.image_intelligence.diagrams.analyzer import DiagramAnalyzer
from app.modules.image_intelligence.generators.canonical_json import ImageJSONGenerator
from app.modules.image_intelligence.generators.markdown_report import ImageMarkdownGenerator
from app.modules.image_intelligence.generators.ocr_exporter import ImageOCRExporter
from app.modules.image_intelligence.metadata.extractor import ImageMetadataExtractor
from app.modules.image_intelligence.ocr.engine import ImageOCREngine
from app.modules.image_intelligence.pipeline import ImageIntelligencePipeline
from app.modules.image_intelligence.preprocessing.pipeline import ImagePreprocessor
from app.modules.image_intelligence.schemas.image_document import (
    ImageDocument,
    ImageRegion,
    RegionType,
)
from app.modules.image_intelligence.vision.engine import VisionIntelligenceEngine


@pytest.fixture
def sample_png_path(tmp_path: Path) -> Path:
    """Create a synthetic PNG image with solid colors."""
    p = tmp_path / "test_sample.png"
    img = Image.new("RGBA", (300, 200), color=(255, 100, 50, 200))
    img.save(p, "PNG")
    return p


@pytest.fixture
def sample_jpeg_path(tmp_path: Path) -> Path:
    """Create a synthetic JPEG image."""
    p = tmp_path / "test_photo.jpg"
    img = Image.new("RGB", (400, 300), color=(40, 120, 200))
    img.save(p, "JPEG")
    return p


@pytest.fixture
def sample_webp_path(tmp_path: Path) -> Path:
    """Create a synthetic WEBP image."""
    p = tmp_path / "test_graphic.webp"
    img = Image.new("RGB", (250, 250), color=(100, 200, 100))
    img.save(p, "WEBP")
    return p


@pytest.fixture
def sample_tiff_path(tmp_path: Path) -> Path:
    """Create a synthetic TIFF image."""
    p = tmp_path / "test_scan.tiff"
    img = Image.new("RGB", (320, 240), color=(240, 240, 240))
    img.save(p, "TIFF")
    return p


@pytest.fixture
def sample_bmp_path(tmp_path: Path) -> Path:
    """Create a synthetic BMP image."""
    p = tmp_path / "test_bitmap.bmp"
    img = Image.new("RGB", (180, 120), color=(20, 20, 20))
    img.save(p, "BMP")
    return p


@pytest.fixture
def sample_svg_path(tmp_path: Path) -> Path:
    """Create a synthetic SVG vector file."""
    p = tmp_path / "test_vector.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <rect width="600" height="400" fill="#f0f4f8"/>
      <circle cx="300" cy="200" r="80" fill="#3b82f6"/>
      <text x="300" y="200" font-size="20" text-anchor="middle" fill="#ffffff">Architecture</text>
    </svg>"""
    p.write_text(svg_content, encoding="utf-8")
    return p


@pytest.fixture
def sample_animated_gif_path(tmp_path: Path) -> Path:
    """Create an animated 2-frame GIF image."""
    p = tmp_path / "test_animation.gif"
    frame1 = Image.new("RGB", (100, 100), color="red")
    frame2 = Image.new("RGB", (100, 100), color="blue")
    frame1.save(p, save_all=True, append_images=[frame2], duration=200, loop=0)
    return p


class TestImageMetadataExtractor:
    """Verify metadata extraction across all 7 supported formats with EXIF sanitization."""

    def test_extract_png_metadata(self, sample_png_path: Path):
        meta = ImageMetadataExtractor.extract(sample_png_path, "png")
        assert meta.format == "png"
        assert meta.width == 300
        assert meta.height == 200
        assert meta.aspect_ratio == 1.5
        assert meta.color_mode == "RGBA"
        assert meta.channels == 4
        assert meta.has_transparency is True
        assert meta.gps_redacted is True

    def test_extract_jpeg_metadata(self, sample_jpeg_path: Path):
        meta = ImageMetadataExtractor.extract(sample_jpeg_path, "jpeg")
        assert meta.format == "jpeg"
        assert meta.width == 400
        assert meta.height == 300
        assert meta.color_mode == "RGB"
        assert meta.channels == 3
        assert meta.has_transparency is False

    def test_extract_webp_metadata(self, sample_webp_path: Path):
        meta = ImageMetadataExtractor.extract(sample_webp_path, "webp")
        assert meta.format == "webp"
        assert meta.width == 250
        assert meta.height == 250
        assert meta.aspect_ratio == 1.0

    def test_extract_tiff_metadata(self, sample_tiff_path: Path):
        meta = ImageMetadataExtractor.extract(sample_tiff_path, "tiff")
        assert meta.format == "tiff"
        assert meta.width == 320
        assert meta.height == 240

    def test_extract_bmp_metadata(self, sample_bmp_path: Path):
        meta = ImageMetadataExtractor.extract(sample_bmp_path, "bmp")
        assert meta.format == "bmp"
        assert meta.width == 180
        assert meta.height == 120

    def test_extract_svg_metadata(self, sample_svg_path: Path):
        meta = ImageMetadataExtractor.extract(sample_svg_path, "svg")
        assert meta.format == "svg"
        assert meta.width == 600
        assert meta.height == 400
        assert meta.has_transparency is True
        assert meta.exif_scrubbed.get("is_vector") is True

    def test_extract_animated_gif_metadata(self, sample_animated_gif_path: Path):
        meta = ImageMetadataExtractor.extract(sample_animated_gif_path, "gif")
        assert meta.is_animated is True
        assert meta.frame_count == 2


class TestImagePreprocessor:
    """Verify non-destructive preprocessing, binarization, deskewing, and tiling."""

    def test_preprocessing_pipeline_raster(self, sample_png_path: Path):
        preprocessor = ImagePreprocessor(max_dimension=1024)
        bundle = preprocessor.process(sample_png_path)

        assert isinstance(bundle.working_image, Image.Image)
        assert isinstance(bundle.ocr_image, Image.Image)
        assert bundle.working_image.mode == "RGB"
        assert bundle.ocr_image.mode == "L"
        assert len(bundle.applied_steps) >= 2
        # Original remains untouched
        with Image.open(sample_png_path) as orig:
            assert orig.mode == "RGBA"

    def test_large_image_tiling(self):
        # Create 2000x2000 image
        large_img = Image.new("RGB", (2000, 2000), color="white")
        preprocessor = ImagePreprocessor(tile_size=1000, tile_overlap_ratio=0.1)
        bundle = preprocessor.process(large_img, enable_tiling=True)

        assert len(bundle.tiles) > 1
        first_tile = bundle.tiles[0]
        assert "pixel_box" in first_tile
        assert "normalized_box" in first_tile
        assert isinstance(first_tile["image"], Image.Image)


class TestImageOCREngine:
    """Verify OCR handling, coordinate normalization, reading order, and graceful fallback."""

    def test_ocr_engine_fallback_when_unavailable(self):
        engine = ImageOCREngine(tesseract_cmd="/non/existent/path/tesseract")
        img = Image.new("RGB", (200, 100), color="white")
        regions, text, conf, warnings = engine.extract_regions(img)

        assert regions == []
        assert text == ""
        assert conf == 0.0
        assert len(warnings) > 0
        assert "unavailable" in warnings[0].lower()

    def test_sort_reading_order_multiline(self):
        engine = ImageOCREngine()
        # Words on line 1: y ~ 20; Words on line 2: y ~ 60
        raw_words = [
            {
                "text": "World",
                "conf": 0.9,
                "x0": 70,
                "y0": 20,
                "x1": 120,
                "y1": 35,
                "line_num": 1,
                "block_num": 1,
            },
            {
                "text": "Hello",
                "conf": 0.95,
                "x0": 10,
                "y0": 22,
                "x1": 60,
                "y1": 36,
                "line_num": 1,
                "block_num": 1,
            },
            {
                "text": "DocuMind",
                "conf": 0.88,
                "x0": 10,
                "y0": 60,
                "x1": 80,
                "y1": 75,
                "line_num": 2,
                "block_num": 1,
            },
        ]
        sorted_words = engine._sort_reading_order(raw_words)
        texts = [w["text"] for w in sorted_words]
        # Line 1: Hello World; Line 2: DocuMind
        assert texts == ["Hello", "World", "DocuMind"]


class TestVisionIntelligenceEngine:
    """Verify scene understanding, captioning, object detection, and grounded VQA."""

    def test_scene_analysis_document_like(self):
        engine = VisionIntelligenceEngine()
        # Mostly white image with text
        img = Image.new("RGB", (600, 800), color=(250, 250, 250))
        caption, scene_type, objects, colors, regions = engine.analyze_scene(
            img,
            ocr_text="Executive Summary and Financial Results for Fiscal Year 2026",
        )
        assert scene_type == "document_page"
        assert "text_document" in objects
        assert len(colors) > 0
        assert len(caption) > 10

    def test_grounded_vqa_text_query(self):
        engine = VisionIntelligenceEngine()
        img = Image.new("RGB", (400, 300), color="white")
        ocr_region = ImageRegion(
            region_id="reg_text_1",
            region_type=RegionType.TEXT,
            bounding_box=[0.1, 0.1, 0.2, 0.4],
            label="text_word",
            text="Revenue",
            confidence=0.98,
            provenance="ocr",
        )
        res = engine.answer_question(
            img=img,
            question="What is written in the header?",
            ocr_text="Total Revenue Q4 2026",
            regions=[ocr_region],
        )
        assert "revenue" in res.answer.lower()
        assert res.confidence > 0.8

    def test_grounded_vqa_chart_query(self):
        engine = VisionIntelligenceEngine()
        img = Image.new("RGB", (400, 300), color="white")
        chart_info = {
            "is_chart": True,
            "chart_type": "bar",
            "title": "Quarterly Performance",
            "series_data": [{"label": "Q1", "value": 120.0}, {"label": "Q2", "value": 150.0}],
        }
        res = engine.answer_question(
            img=img,
            question="What chart is shown and what are the trends?",
            chart_info=chart_info,
        )
        assert "bar" in res.answer.lower()
        assert "quarterly performance" in res.answer.lower()
        assert "120" in res.answer or "150" in res.answer


class TestDiagramAndChartAnalyzers:
    """Verify structural analysis for technical diagrams and statistical charts."""

    def test_diagram_analyzer_flowchart_detection(self):
        analyzer = DiagramAnalyzer()
        img = Image.new("RGB", (500, 400), color="white")
        ocr_text = "Start -> Validate Input -> Decision -> Process Order -> End"
        text_regions = [
            ImageRegion(
                region_id="n1",
                region_type=RegionType.TEXT,
                bounding_box=[0.1, 0.1, 0.2, 0.3],
                label="Start",
                text="Start",
                confidence=0.95,
                provenance="ocr",
            ),
            ImageRegion(
                region_id="n2",
                region_type=RegionType.TEXT,
                bounding_box=[0.7, 0.1, 0.8, 0.3],
                label="End",
                text="End",
                confidence=0.95,
                provenance="ocr",
            ),
        ]
        diag, regions = analyzer.analyze(img, ocr_text, text_regions)
        assert diag.is_diagram is True
        assert diag.diagram_type == "flowchart"
        assert diag.flow_direction == "top-to-bottom"
        assert len(diag.nodes) == 2
        assert len(regions) == 2

    def test_chart_analyzer_pie_chart_detection(self):
        analyzer = ChartAnalyzer()
        img = Image.new("RGB", (500, 400), color="white")
        ocr_text = "Market Share Distribution: Product A 45%, Product B 35%, Product C 20%"
        chart, regions = analyzer.analyze(img, ocr_text, [])
        assert chart.is_chart is True
        assert chart.chart_type == "pie"
        assert len(chart.series_data) >= 3
        assert chart.series_data[0]["value"] == 45.0
        assert len(regions) >= 1


class TestImageOutputGenerators:
    """Verify canonical JSON, Markdown report, manifest, and OCR text export."""

    def test_generate_outputs_complete_lifecycle(self, sample_png_path: Path):
        pipeline = ImageIntelligencePipeline()
        image_doc, manifest = pipeline.process_image_path(
            file_path=sample_png_path,
            file_id="test-lifecycle-id",
            filename="sample.png",
            format_id="png",
        )

        assert isinstance(image_doc, ImageDocument)
        assert manifest.file_id == "test-lifecycle-id"

        # 1. Canonical JSON
        json_output = ImageJSONGenerator.generate(image_doc)
        assert '"format": "png"' in json_output
        assert '"image_id":' in json_output

        # 2. Markdown Report
        md_output = ImageMarkdownGenerator.generate(image_doc)
        assert "# Visual Intelligence Report:" in md_output
        assert "## 1. Visual Scene Summary" in md_output
        assert "GPS Privacy Scrubbing:" in md_output

        # 3. OCR Text Export
        ocr_output = ImageOCRExporter.export(image_doc)
        assert isinstance(ocr_output, str)
