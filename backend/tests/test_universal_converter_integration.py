import subprocess
import sys
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
_engine = _root / "converter_engine"
if str(_engine) not in sys.path:
    sys.path.insert(0, str(_engine))

from app.modules.converters.adapters.converter_engine_adapter import ConverterEngineAdapter  # noqa: E402
from app.modules.converters.service import UniversalConversionService  # noqa: E402


@pytest.mark.asyncio
async def test_converter_engine_adapter_basic():
    """Verify that ConverterEngineAdapter correctly maps document blocks and properties."""
    from converter_engine.common.models import Document, HeadingBlock, ParagraphBlock, TableBlock

    doc = Document(
        source="/test/file.txt",
        source_type="text",
        title="Sample Test Doc",
        text="Heading 1\n\nParagraph text here.",
    )
    doc.blocks = [
        HeadingBlock(type="heading", level=1, text="Main Heading"),
        ParagraphBlock(type="paragraph", text="Body text paragraph for testing."),
        TableBlock(type="table", headers=["A", "B"], rows=[["1", "2"]], caption="Sample Table"),
    ]

    univ = ConverterEngineAdapter.adapt(doc, "sample_test.txt", "text")
    assert univ.title == "Sample Test Doc"
    assert len(univ.sections) >= 1
    assert univ.sections[0].title == "Main Heading"
    assert len(univ.tables) == 1
    assert univ.tables[0].headers == ["A", "B"]


@pytest.mark.asyncio
async def test_html_conversion_via_service(tmp_path: Path):
    """Verify that HTML files are parsed and extracted cleanly via converter_engine."""
    html_file = tmp_path / "page.html"
    html_file.write_text(
        "<html><head><title>Test HTML Page</title></head>"
        "<body><h1>Header One</h1><p>Description inside page.</p></body></html>"
    )

    service = UniversalConversionService()
    record = await service.convert_file(
        file_path=html_file,
        target_format="md",
        extraction_mode="structured_text",
        original_filename="page.html",
    )

    assert record.status == "completed"
    assert record.source_format == "html"
    assert "Header One" in record.preview_content
    assert "Description inside page" in record.preview_content


def test_root_cli_help():
    """Verify that python main.py runs properly from project root."""
    res = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert res.returncode == 0
    assert "Universal Document Processor" in res.stdout
    assert "--input" in res.stdout
