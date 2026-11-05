"""Unit tests for plugin architecture, interface contracts, and registry."""

from pathlib import Path

import pytest

from app.plugins.interfaces.ai import CompletionRequest
from app.plugins.interfaces.base import PluginType
from app.plugins.registry.registry import PluginRegistry
from app.plugins.samples.mock_ai_provider import MockLocalAIProvider
from app.plugins.samples.mock_detector import MockTextDetectorPlugin
from app.plugins.samples.mock_extractor import MockTextExtractorPlugin
from app.plugins.samples.mock_formatter import MockMarkdownFormatter


@pytest.mark.asyncio
async def test_plugin_registration_and_retrieval():
    registry = PluginRegistry()
    detector = MockTextDetectorPlugin()
    extractor = MockTextExtractorPlugin()
    ai_provider = MockLocalAIProvider()

    registry.register(detector)
    registry.register(extractor)
    registry.register(ai_provider)

    assert registry.get_plugin("mock_text_detector") is not None
    assert registry.get_detector("mock_text_detector") is not None
    assert registry.get_extractor("mock_text_extractor") is not None
    assert registry.get_ai_provider("mock_local_ai_provider") is not None

    plugins = registry.list_plugins()
    assert len(plugins) == 3

    detectors = registry.list_plugins(plugin_type=PluginType.DETECTOR)
    assert len(detectors) == 1
    assert detectors[0].name == "mock_text_detector"


@pytest.mark.asyncio
async def test_plugin_format_matching():
    registry = PluginRegistry()
    extractor = MockTextExtractorPlugin()
    registry.register(extractor)

    matches_txt = registry.find_extractors_for_format("txt")
    assert len(matches_txt) == 1
    assert matches_txt[0].metadata.name == "mock_text_extractor"

    matches_pdf = registry.find_extractors_for_format("pdf")
    assert len(matches_pdf) == 0


@pytest.mark.asyncio
async def test_mock_detector_execution(tmp_path: Path):
    detector = MockTextDetectorPlugin()
    sample_file = tmp_path / "test.txt"
    sample_file.write_text("Hello DocuMind AI")

    result = await detector.detect(sample_file)
    assert result.mime_type == "text/plain"
    assert result.extension == "txt"
    assert result.confidence > 0.9


@pytest.mark.asyncio
async def test_mock_extractor_execution(tmp_path: Path):
    extractor = MockTextExtractorPlugin()
    sample_file = tmp_path / "doc.md"
    sample_file.write_text("# Title\n\nSample Markdown content.")

    result = await extractor.extract(sample_file)
    assert result.engine_name == "mock_text_extractor"
    assert len(result.elements) > 0
    assert "Sample Markdown content" in result.raw_text


@pytest.mark.asyncio
async def test_mock_ai_provider_execution():
    ai = MockLocalAIProvider()
    assert ai.is_cloud is False

    response = await ai.complete(CompletionRequest(prompt="Summarize this file"))
    assert response.model_used is not None
    assert "Mock Local AI Summary" in response.content

    embeddings = await ai.embed(["Hello world", "DocuMind AI"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 16


@pytest.mark.asyncio
async def test_mock_formatter_execution():
    formatter = MockMarkdownFormatter()
    # Create extraction result
    from app.plugins.interfaces.extractor import ExtractedElement, ExtractionResult

    result = ExtractionResult(
        engine_name="test_engine",
        elements=[ExtractedElement(element_type="text", content="Formatted text")],
        raw_text="Formatted text",
        page_count=2,
    )
    formatted_bytes = await formatter.format(result)
    text = formatted_bytes.decode("utf-8")
    assert "# Extracted Document" in text
    assert "Formatted text" in text
