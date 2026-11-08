"""Comprehensive Unit and Integration Tests for Universal File Converter and Extractor."""

import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from app.modules.converters import (
    ConversionStatus,
    UniversalCodeBlock,
    UniversalContent,
    UniversalConversionService,
    UniversalSection,
    UniversalTable,
    UniversalTranscriptSegment,
)
from app.modules.converters.writers import (
    BundleWriter,
    CsvWriter,
    HtmlWriter,
    JsonWriter,
    MarkdownWriter,
    SubtitleWriter,
    TxtWriter,
)


@pytest.fixture
def sample_universal_content() -> UniversalContent:
    """Fixture providing rich multimodal UniversalContent."""
    return UniversalContent(
        source_filename="quarterly_report.pdf",
        source_format="pdf",
        title="DocuMind Q4 Report",
        author="Architecture Team",
        page_count=3,
        word_count=120,
        paragraphs=[
            "This report summarizes system performance and conversion metrics.",
            "All engines demonstrated zero regressions under load.",
        ],
        sections=[
            UniversalSection(
                title="Executive Summary",
                level=1,
                content="DocuMind achieved 99.8% extraction fidelity across 60+ formats.",
                page_or_slide_number=1,
            ),
            UniversalSection(
                title="Performance Benchmarks",
                level=2,
                content="P95 latency remained under 250ms for documents under 50MB.",
                page_or_slide_number=2,
            ),
        ],
        tables=[
            UniversalTable(
                title="Financial Figures",
                sheet_name="Q4 Summary",
                headers=["Department", "Budget", "Delta", "Formula Attack"],
                rows=[
                    ["Engineering", 150000, -4250.50, "=cmd|' /C calc'!A0"],
                    ["Infrastructure", 80000, -100, "-2+3*cmd"],
                    ["Operations", 45000, +2500, "@SUM(A1:B10)"],
                ],
                row_count=3,
                col_count=4,
            )
        ],
        code_blocks=[
            UniversalCodeBlock(
                language="python",
                code="def convert_file(path):\n    return True\n",
                caption="Main Pipeline Entry",
                line_count=2,
            )
        ],
        transcript_segments=[
            UniversalTranscriptSegment(
                start_seconds=0.0,
                end_seconds=4.5,
                speaker="Speaker 1",
                text="Welcome to the universal file conversion review.",
                confidence=0.98,
            ),
            UniversalTranscriptSegment(
                start_seconds=4.5,
                end_seconds=8.2,
                speaker="Speaker 2",
                text="All extraction pipelines are verified.",
                confidence=0.99,
            ),
        ],
        metadata={"created_year": 2026, "department": "Platform"},
        warnings=[],
        raw_text="DocuMind Q4 Report\nExecutive Summary\nPerformance Benchmarks",
    )


class TestWriters:
    """Tests for all format writers."""

    def test_txt_writer(self, sample_universal_content: UniversalContent):
        output = TxtWriter.write(sample_universal_content)
        assert "DocuMind Q4 Report" in output
        assert "Author: Architecture Team" in output
        assert "Executive Summary" in output
        assert "Welcome to the universal file conversion review." in output
        assert "[CODE: Main Pipeline Entry]" in output or "def convert_file" in output
        assert "Engineering" in output

    def test_markdown_writer(self, sample_universal_content: UniversalContent):
        output = MarkdownWriter.write(sample_universal_content)
        assert "# DocuMind Q4 Report" in output
        assert "# Executive Summary *(# 1)*" in output
        assert "## Performance Benchmarks *(# 2)*" in output
        assert "| Department | Budget | Delta | Formula Attack |" in output
        assert "```python" in output
        assert "def convert_file" in output
        assert "`00:00`" in output or "00:00" in output

    def test_json_writer(self, sample_universal_content: UniversalContent):
        output = JsonWriter.write(sample_universal_content)
        data = json.loads(output)
        assert data["version"] == "2.0.0"
        assert data["document"]["title"] == "DocuMind Q4 Report"
        assert len(data["content"]["sections"]) == 2
        assert len(data["content"]["tables"]) == 1
        assert len(data["content"]["code_blocks"]) == 1
        assert len(data["content"]["transcript_segments"]) == 2

    def test_csv_writer_formula_injection_defense(self, sample_universal_content: UniversalContent):
        """CRITICAL REQUIREMENT:

        Prevent spreadsheet formula injection in exported CSV files without
        corrupting legitimate negative numeric values.
        """
        # Test individual cells
        # 1. Legitimate negative numbers MUST NOT be corrupted with single quote (')
        assert CsvWriter.sanitize_cell(-4250.50) == -4250.50
        assert CsvWriter.sanitize_cell("-4250.50") == "-4250.50"
        assert CsvWriter.sanitize_cell("-100") == "-100"
        assert CsvWriter.sanitize_cell(-100) == -100
        assert CsvWriter.sanitize_cell("-0.005") == "-0.005"

        # 2. Legitimate positive signed numbers MUST NOT be corrupted
        assert CsvWriter.sanitize_cell("+2500") == "+2500"
        assert CsvWriter.sanitize_cell(2500) == 2500

        # 3. Dangerous formulas starting with =, +, -, @ MUST be escaped with (')
        assert CsvWriter.sanitize_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
        assert CsvWriter.sanitize_cell("=1+1") == "'=1+1"
        assert CsvWriter.sanitize_cell("-2+3*cmd") == "'-2+3*cmd"
        assert CsvWriter.sanitize_cell("@SUM(A1:B10)") == "'@SUM(A1:B10)"
        assert CsvWriter.sanitize_cell("\tMALICIOUS") == "'\tMALICIOUS"

        # Test full CSV output
        csv_str = CsvWriter.write(sample_universal_content)
        lines = csv_str.strip().split("\n")
        assert "Department,Budget,Delta,Formula Attack" in lines[0]
        # Legitimate negative number -4250.5 is preserved
        assert "-4250.5" in lines[1]
        # Dangerous formula is neutralized
        assert "'=cmd|' /C calc'!A0" in lines[1]
        # Malicious -2+3*cmd is neutralized
        assert "'-2+3*cmd" in lines[2]
        # Malicious @SUM is neutralized
        assert "'@SUM(A1:B10)" in lines[3]

    def test_html_writer_xss_protection(self):
        """Ensure all user/document content is properly escaped in HTML."""
        malicious_content = UniversalContent(
            source_filename="<script>alert(1)</script>.pdf",
            source_format="pdf",
            title="<img src=x onerror=alert('xss')>",
            paragraphs=["<svg onload=alert(2)>", "Normal paragraph"],
            tables=[
                UniversalTable(
                    title="<script>evil()</script>",
                    headers=["<col1>", "col2"],
                    rows=[["<a href='javascript:alert(1)'>click</a>", "safe"]],
                )
            ],
            code_blocks=[
                UniversalCodeBlock(
                    language="html",
                    code="<script>console.log('code block')</script>",
                    caption="Code Caption",
                )
            ],
        )

        html_out = HtmlWriter.write(malicious_content)
        # Verify no unescaped dangerous tags
        assert "<script>alert(1)</script>" not in html_out
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out
        assert "<img src=x onerror=alert('xss')>" not in html_out
        assert "&lt;img src=x onerror=alert(&#x27;xss&#x27;)&gt;" in html_out
        assert "<svg onload=alert(2)>" not in html_out
        assert "<!DOCTYPE html>" in html_out

    def test_subtitles_srt_and_vtt(self, sample_universal_content: UniversalContent):
        srt = SubtitleWriter.write_srt(sample_universal_content)
        assert "00:00:00,000 --> 00:00:04,500" in srt
        assert "Welcome to the universal file conversion review." in srt
        assert "00:00:04,500 --> 00:00:08,200" in srt

        vtt = SubtitleWriter.write_vtt(sample_universal_content)
        assert vtt.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:04.500" in vtt
        assert "<v Speaker 1>Welcome to the universal file conversion review.</v>" in vtt

    def test_mode_c_bundle_writer(self, sample_universal_content: UniversalContent):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "bundle.zip"
            size = BundleWriter.write_zip(sample_universal_content, zip_path)
            assert size > 0
            assert zip_path.exists()

            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                assert "quarterly_report.txt" in names
                assert "quarterly_report.md" in names
                assert "quarterly_report.json" in names
                assert "quarterly_report.html" in names
                assert "metadata.json" in names
                assert "manifest.json" in names
                assert any(n.startswith("tables/") for n in names)
                assert "subtitles/transcript.srt" in names
                assert "subtitles/transcript.vtt" in names


class TestUniversalConversionService:
    """Tests for the end-to-end service orchestration."""

    @pytest.mark.asyncio
    async def test_capabilities_matrix(self):
        service = UniversalConversionService()
        caps = service.get_supported_capabilities()
        assert len(caps) >= 50
        formats = [c.input_format for c in caps]
        assert "pdf" in formats
        assert "docx" in formats
        assert "xlsx" in formats
        assert "pptx" in formats
        assert "png" in formats
        assert "mp3" in formats
        assert "mp4" in formats
        assert "py" in formats
        assert "json" in formats
        assert "zip" in formats

    @pytest.mark.asyncio
    async def test_convert_markdown_file(self):
        service = UniversalConversionService()
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(b"# Title\n\nParagraph 1.\n\n| H1 | H2 |\n|---|---|\n| 1 | 2 |\n")
            path = Path(f.name)

        try:
            # Mode A: TXT
            rec_txt = await service.convert_file(
                file_path=path,
                target_format="txt",
                extraction_mode="plain_text",
                original_filename="sample.md",
            )
            assert rec_txt.status == ConversionStatus.COMPLETED.value
            assert rec_txt.output_filename.endswith(".txt")
            assert "Title" in rec_txt.preview_content

            # Mode B: MD
            rec_md = await service.convert_file(
                file_path=path,
                target_format="md",
                extraction_mode="structured_text",
                original_filename="sample.md",
            )
            assert rec_md.status == ConversionStatus.COMPLETED.value
            assert rec_md.output_filename.endswith(".md")
            assert "# Title" in rec_md.preview_content

            # Mode C: ZIP Bundle
            rec_zip = await service.convert_file(
                file_path=path,
                target_format="zip",
                extraction_mode="complete",
                original_filename="sample.md",
            )
            assert rec_zip.status == ConversionStatus.COMPLETED.value
            assert rec_zip.output_filename.endswith(".zip")
            assert Path(rec_zip.output_path).exists()
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_convert_code_file(self):
        service = UniversalConversionService()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"def compute_total(a: int, b: int) -> int:\n    return a + b\n")
            path = Path(f.name)

        try:
            rec = await service.convert_file(
                file_path=path,
                target_format="html",
                extraction_mode="structured_text",
                original_filename="math_util.py",
            )
            assert rec.status == ConversionStatus.COMPLETED.value
            assert rec.output_filename.endswith(".html")
            assert "compute_total" in rec.preview_content
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_convert_structured_json_file(self):
        service = UniversalConversionService()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b'[{"name": "Alice", "role": "Engineer"}, {"name": "Bob", "role": "Designer"}]')
            path = Path(f.name)

        try:
            rec = await service.convert_file(
                file_path=path,
                target_format="csv",
                extraction_mode="structured_text",
                original_filename="users.json",
            )
            assert rec.status == ConversionStatus.COMPLETED.value
            assert rec.output_filename.endswith(".csv")
            assert "name" in rec.preview_content or "Alice" in rec.preview_content
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_convert_image_scan_to_txt_and_md(self):
        from PIL import Image, ImageDraw

        service = UniversalConversionService()

        img = Image.new("RGB", (400, 100), color="white")
        d = ImageDraw.Draw(img)
        d.text((10, 30), "DocuMind Scan OCR", fill="black")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name)
            path = Path(f.name)

        try:
            # 1. Image scan to TXT
            rec_txt = await service.convert_file(
                file_path=path,
                target_format="txt",
                original_filename="scan.png",
            )
            assert rec_txt.status == ConversionStatus.COMPLETED.value
            assert rec_txt.output_filename.endswith(".txt")
            assert "Scan" in rec_txt.preview_content or "OCR" in rec_txt.preview_content

            # 2. Image scan to MD
            rec_md = await service.convert_file(
                file_path=path,
                target_format="md",
                original_filename="scan.png",
            )
            assert rec_md.status == ConversionStatus.COMPLETED.value
            assert rec_md.output_filename.endswith(".md")
            assert "Scan" in rec_md.preview_content or "OCR" in rec_md.preview_content
        finally:
            path.unlink(missing_ok=True)
