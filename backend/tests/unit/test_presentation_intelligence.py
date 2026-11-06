"""Unit tests for Phase 6 Presentation Intelligence Engine."""

from pathlib import Path

import pytest

from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.presentation_intelligence.adapters.odp_adapter import ODPPresentationAdapter
from app.modules.presentation_intelligence.adapters.ppt_adapter import PPTPresentationAdapter
from app.modules.presentation_intelligence.adapters.pptx_adapter import PPTXPresentationAdapter
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
from app.modules.presentation_intelligence.pipeline import (
    UnsupportedPresentationFormatError,
    presentation_pipeline,
)
from app.modules.presentation_intelligence.schemas.presentation_document import (
    ChartType,
    ElementType,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "presentations"


class TestPresentationPipelineUnit:
    """Test suite for Presentation Intelligence Pipeline routing and capabilities."""

    def test_pipeline_supported_formats(self) -> None:
        formats = presentation_pipeline.list_supported_formats()
        assert "pptx" in formats
        assert "ppt" in formats
        assert "odp" in formats

    def test_pipeline_get_adapter(self) -> None:
        pptx_ad = presentation_pipeline.get_adapter("pptx")
        assert isinstance(pptx_ad, PPTXPresentationAdapter)

        ppt_ad = presentation_pipeline.get_adapter("ppt")
        assert isinstance(ppt_ad, PPTPresentationAdapter)

        odp_ad = presentation_pipeline.get_adapter("odp")
        assert isinstance(odp_ad, ODPPresentationAdapter)

    def test_pipeline_unsupported_format_raises(self) -> None:
        with pytest.raises(UnsupportedPresentationFormatError):
            presentation_pipeline.get_adapter("invalid_fmt")


class TestUniversalDetectorPresentationFormats:
    """Test multi-signal file detection on presentation formats."""

    def setup_method(self) -> None:
        self.detector = UniversalFileDetector()

    def test_detect_pptx(self) -> None:
        path = FIXTURES_DIR / "pptx_basic_text.pptx"
        res = self.detector.detect_file(path, original_filename="slides.pptx")
        assert res.format_id == "pptx"
        assert res.is_valid is True
        assert res.is_corrupted is False

    def test_detect_odp(self) -> None:
        path = FIXTURES_DIR / "odp_text_tables.odp"
        res = self.detector.detect_file(path, original_filename="deck.odp")
        assert res.format_id == "odp"
        assert res.is_valid is True

    def test_detect_legacy_ppt(self) -> None:
        path = FIXTURES_DIR / "legacy_powerpoint.ppt"
        res = self.detector.detect_file(path, original_filename="legacy.ppt")
        assert res.format_id == "ppt"
        assert res.is_valid is True

    def test_detect_corrupted_presentation(self) -> None:
        path = FIXTURES_DIR / "corrupted_presentation.pptx"
        res = self.detector.detect_file(path, original_filename="corrupted.pptx")
        assert res.is_corrupted is True


class TestPPTXExtractionFeatures:
    """Test specific extraction capabilities on PPTX presentations."""

    @pytest.mark.asyncio
    async def test_extract_basic_text_and_layouts(self) -> None:
        path = FIXTURES_DIR / "pptx_basic_text.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert doc.slide_count == 2
        assert len(doc.slides) == 2
        assert "Architecture" in (doc.slides[0].title or "")
        assert any("Modular Monolith" in (e.text or "") for e in doc.slides[1].elements)

    @pytest.mark.asyncio
    async def test_extract_nested_bullet_hierarchy(self) -> None:
        path = FIXTURES_DIR / "pptx_nested_bullets.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        slide = doc.slides[0]
        text_elems = [e for e in slide.elements if e.element_type == ElementType.TEXT]
        assert len(text_elems) > 0

        # Verify bullet nesting levels
        paras = text_elems[0].paragraphs
        levels = [p.level for p in paras]
        assert 0 in levels
        assert 1 in levels
        assert 2 in levels

    @pytest.mark.asyncio
    async def test_extract_tables(self) -> None:
        path = FIXTURES_DIR / "pptx_tables.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert len(doc.tables) >= 1
        tbl = doc.tables[0]
        assert tbl.rows_count == 4
        assert tbl.columns_count == 3
        assert "Quarter" in tbl.headers
        assert tbl.has_header is True

    @pytest.mark.asyncio
    async def test_extract_native_charts(self) -> None:
        path = FIXTURES_DIR / "pptx_native_charts.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert len(doc.charts) >= 1
        ch = doc.charts[0]
        assert ch.chart_type == ChartType.COLUMN
        assert "North America" in ch.categories
        assert len(ch.series) >= 2
        assert ch.series[0].name == "2025"
        assert ch.series[0].values[0] == 40.5

    @pytest.mark.asyncio
    async def test_extract_images(self) -> None:
        path = FIXTURES_DIR / "pptx_images.pptx"
        doc, raw_assets = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert len(doc.assets) >= 1
        assert len(raw_assets) >= 1
        asset = doc.assets[0]
        assert asset.format in ("png", "jpeg")
        assert asset.size_bytes > 0
        assert len(asset.sha256) == 64

    @pytest.mark.asyncio
    async def test_extract_speaker_notes(self) -> None:
        path = FIXTURES_DIR / "pptx_speaker_notes.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert len(doc.speaker_notes) >= 1
        note = doc.speaker_notes[0]
        assert "CFO sign-off" in note.text
        assert note.word_count > 0

    @pytest.mark.asyncio
    async def test_extract_hidden_slides(self) -> None:
        path = FIXTURES_DIR / "pptx_hidden_slides.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        assert doc.slide_count == 3
        assert doc.metadata.hidden_slide_count == 1
        hidden_slides = [s for s in doc.slides if s.hidden]
        assert len(hidden_slides) == 1
        assert "Backup" in (hidden_slides[0].title or "")

    @pytest.mark.asyncio
    async def test_extract_unicode_hindi(self) -> None:
        path = FIXTURES_DIR / "pptx_unicode_hindi.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )
        slide = doc.slides[0]
        assert any("नमस्ते दुनिया" in (e.text or "") for e in slide.elements)


class TestODPExtraction:
    """Test native OpenDocument Presentation (.odp) extraction."""

    @pytest.mark.asyncio
    async def test_extract_odp_presentation(self) -> None:
        path = FIXTURES_DIR / "odp_text_tables.odp"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="odp", original_filename=path.name
        )
        assert doc.format == "odp"
        assert doc.slide_count >= 1
        assert "OpenDocument" in (doc.metadata.title or "")
        # Table extraction
        assert len(doc.tables) >= 1
        assert doc.tables[0].headers == ["Component", "Status"]
        # Speaker notes
        assert len(doc.speaker_notes) >= 1
        assert "OpenDocument" in doc.speaker_notes[0].text


class TestLegacyPPTExtraction:
    """Test legacy binary PowerPoint (.ppt) extraction."""

    @pytest.mark.asyncio
    async def test_extract_legacy_ppt_binary(self) -> None:
        path = FIXTURES_DIR / "legacy_powerpoint.ppt"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="ppt", original_filename=path.name
        )
        assert doc.format == "ppt"
        assert doc.slide_count >= 1
        assert doc.extraction_metadata.get("engine_name") in ("ole2-binary-parser", "libreoffice-headless")
        # Verify text extracted from binary stream
        all_text = " ".join(e.text or "" for s in doc.slides for e in s.elements)
        assert "Executive Review 2003" in all_text


class TestPresentationGenerators:
    """Test output generation across JSON, Markdown, Text, and Manifest."""

    @pytest.mark.asyncio
    async def test_generators_pipeline(self) -> None:
        path = FIXTURES_DIR / "pptx_tables.pptx"
        doc, _ = await presentation_pipeline.extract_document(
            file_path=path, format_id="pptx", original_filename=path.name
        )

        # 1. JSON
        json_str = PresentationJSONGenerator.generate(doc)
        assert "document_id" in json_str
        assert "Quarterly Revenue Summary" in json_str

        # 2. Markdown
        md_str = PresentationMarkdownGenerator.generate(doc)
        assert "# " in md_str
        assert "## Slide 1" in md_str
        assert "| Quarter | Revenue ($M) | Growth |" in md_str

        # 3. Plain Text
        txt_str = PresentationTextGenerator.generate(doc)
        assert "SLIDE 1" in txt_str

        # 4. Manifest
        manifest = PresentationManifestGenerator.generate(
            doc=doc,
            source_filename="pptx_tables.pptx",
            source_format="pptx",
            processing_time_seconds=0.042,
            artifacts={"json": "mock/path.json"},
        )
        assert manifest.slide_count == doc.slide_count
        assert manifest.table_count == 1
        assert manifest.status == "completed"
